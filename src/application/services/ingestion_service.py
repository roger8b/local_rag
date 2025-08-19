"""
Generic Knowledge Ingestion Service for processing any document,
dynamically inferring a graph schema, extracting entities and relationships,
and building a knowledge graph in Neo4j.

Version 3.4 - Fixed Ollama API endpoints and error handling
"""

import asyncio
import inspect
import json
import uuid
from typing import List, Dict, Any
import httpx
from neo4j import GraphDatabase
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config.settings import settings
import os
import logging

logger = logging.getLogger(__name__)


def is_valid_file_type(filename: str) -> bool:
    """Check if the file has a valid extension (txt or pdf)"""
    return filename.lower().endswith(('.txt', '.pdf'))


class IngestionService:
    """
    Service for ingesting documents and building a hybrid knowledge graph.
    This version is generic and infers the schema from the document content.
    """
    
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            try:
                if getattr(settings, 'neo4j_verify_connectivity', True):
                    self.driver.verify_connectivity()
                self._db_disabled = False
                logger.info("Neo4j connection established.")
            except Exception as conn_err:
                logger.warning(f"Neo4j unavailable, running in degraded mode: {conn_err}")
                self._db_disabled = True
        except Exception as e:
            logger.warning(f"Neo4j driver init failed, running in degraded mode: {e}")
            self.driver = None
            self._db_disabled = True
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    async def _check_ollama_health(self) -> bool:
        """Check if Ollama is running and responsive"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.ollama_base_url}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def _check_model_availability(self, model_name: str) -> bool:
        """Check if the specified model is available in Ollama"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.ollama_base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = [model["name"] for model in models]
                    logger.info(f"Available models: {available_models}")
                    return any(model_name in model["name"] for model in models)
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
        return False

    # --- Step 1: Document Graph Creation ---
    def _ensure_vector_index(self):
        if self.driver is None:
            logger.debug("Skipping index check: driver unavailable")
            return
        try:
            with self.driver.session() as session:
                result = session.run("SHOW INDEXES YIELD name WHERE name = 'document_embeddings'")
                if not result.single():
                    query = f"""
                    CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
                    FOR (c:Chunk) ON (c.embedding)
                    OPTIONS {{ indexConfig: {{
                        `vector.dimensions`: {settings.openai_embedding_dimensions},
                        `vector.similarity_function`: 'cosine'
                    }}}}
                    """
                    session.run(query)
                    logger.info("Created vector index 'document_embeddings'.")
        except Exception as e:
            logger.warning(f"Could not ensure vector index due to Neo4j error: {e}")

    def _create_chunks(self, content: str) -> List[str]:
        return self.text_splitter.split_text(content)

    async def _safe_raise_for_status(self, response: Any) -> None:
        """Call response.raise_for_status() handling AsyncMock in tests."""
        try:
            result = response.raise_for_status()
            if asyncio.iscoroutine(result) or inspect.isawaitable(result):
                await result
        except Exception:
            raise

    async def _generate_embeddings(self, chunks: List[str], provider: str = "ollama") -> List[List[float]]:
        """Generate embeddings using the configured provider (ollama or openai)"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks via {provider}...")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if provider == "openai":
                    # Fail fast if API key is missing to avoid network calls in tests
                    api_key = getattr(settings, 'openai_api_key', None)
                    if not api_key:
                        raise ValueError("OPENAI_API_KEY não configurada")
                    payload = {
                        "model": settings.openai_embedding_model,
                        "input": chunks,
                        "dimensions": settings.openai_embedding_dimensions,
                    }
                    response = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                        },
                    )
                    await self._safe_raise_for_status(response)
                    result = response.json()
                    if asyncio.iscoroutine(result):
                        result = await result
                    data = result.get("data", [])
                    all_embeddings = [d.get("embedding", []) for d in data]
                else:
                    response = await client.post(
                        f"{settings.ollama_base_url}/api/embed",
                        json={
                            "model": settings.embedding_model,
                            "input": chunks
                        },
                    )
                    await self._safe_raise_for_status(response)
                    result = response.json()
                    if asyncio.iscoroutine(result):
                        result = await result
                    if "embeddings" not in result:
                        raise ValueError("Invalid response from Ollama embed API, 'embeddings' key not found.")
                    all_embeddings = result["embeddings"]

                if len(all_embeddings) != len(chunks):
                    raise ValueError(f"Mismatch in returned embeddings count. Expected {len(chunks)}, got {len(all_embeddings)}")

            logger.info("Embeddings generated successfully.")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def _save_document_graph(self, chunks: List[Dict[str, Any]], filename: str, document_id: str):
        if self._db_disabled: return
        create_chunks_query = """
        UNWIND $chunks_data AS chunk
        CREATE (c:Chunk { id: chunk.chunk_id, text: chunk.text, embedding: chunk.embedding,
            source_file: $source_file, document_id: $document_id, chunk_index: chunk.chunk_index,
            created_at: datetime() })
        """
        connect_chunks_query = """
        MATCH (c1:Chunk {document_id: $document_id})
        WITH c1 ORDER BY c1.chunk_index
        WITH collect(c1) as chunks
        UNWIND range(0, size(chunks)-2) as i
        WITH chunks[i] as c1, chunks[i+1] as c2
        MERGE (c1)-[r:NEXT]->(c2)
        """
        try:
            with self.driver.session() as session:
                session.run(create_chunks_query, chunks_data=chunks, source_file=filename, document_id=document_id)
                if len(chunks) > 1:
                    session.run(connect_chunks_query, document_id=document_id)
                logger.info(f"Saved document graph for {document_id} with {len(chunks)} chunks.")
        except Exception as e:
            logger.error(f"Error saving document graph: {e}")
            raise

    def _save_to_neo4j(self, chunks: List[str], embeddings: List[List[float]], filename: str) -> str:
        """Save chunks+embeddings using UNWIND and return the document_id.

        If DB is disabled/unavailable, just return the generated document_id.
        """
        document_id = str(uuid.uuid4())
        chunk_data_list = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_data_list.append({
                "chunk_id": f"{document_id}-chunk-{i}",
                "text": chunk_text,
                "embedding": embedding,
                "chunk_index": i,
            })

        try:
            self._save_document_graph(chunk_data_list, filename, document_id)
        except Exception:
            # Already logged upstream; continue returning the id for degraded mode
            pass

        return document_id

    # --- Step 2: Generic Knowledge Graph Extraction ---

    async def _infer_graph_schema(self, content_sample: str) -> Dict[str, List[str]]:
        """Infer a graph schema from a sample of the document"""
        logger.info("Inferring graph schema from document content...")
        
        # Check Ollama health first
        if not await self._check_ollama_health():
            logger.warning("Ollama not available, using fallback schema")
            return {"node_labels": ["Entity", "Concept"], "relationship_types": ["RELATED_TO", "MENTIONS"]}
        
        # Check if model is available
        if not await self._check_model_availability(settings.llm_model):
            logger.warning(f"Model {settings.llm_model} not available, using fallback schema")
            return {"node_labels": ["Entity", "Concept"], "relationship_types": ["RELATED_TO", "MENTIONS"]}
        
        prompt = f"""
        You are an expert data modeler and graph architect. Your task is to analyze the provided text
        and propose a generic, yet effective, graph schema. Identify the main types of entities
        (as node labels) and the types of relationships that connect them.

        Return the result as a single, valid JSON object with two keys:
        1. "node_labels": A list of strings representing the types of entities (e.g., "Person", "Company").
        2. "relationship_types": A list of strings representing the types of relationships (e.g., "WORKS_AT", "INVESTED_IN").

        Do not extract the actual data, only the schema.

        Here is the text to analyze:
        ---
        {content_sample}
        ---

        JSON Schema:
        """
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.llm_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                )
                await self._safe_raise_for_status(response)
                resp_json = response.json()
                if asyncio.iscoroutine(resp_json):
                    resp_json = await resp_json
                response_text = resp_json["response"]
                schema = json.loads(response_text)
                logger.info(f"Inferred schema: {schema}")
                return schema
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during schema inference: {e.response.status_code} - {e.response.text}")
            return {"node_labels": ["Entity", "Concept"], "relationship_types": ["RELATED_TO", "MENTIONS"]}
        except Exception as e:
            logger.error(f"Error during schema inference: {e}")
            return {"node_labels": ["Entity", "Concept"], "relationship_types": ["RELATED_TO", "MENTIONS"]}

    async def _call_ollama_for_extraction(self, chunk_text: str, schema: Dict[str, List[str]]) -> Dict[str, Any]:
        """Call Ollama to extract entities and relationships based on the inferred schema"""
        
        node_labels_str = ", ".join([f'"{label}"' for label in schema.get("node_labels", [])])
        rel_types_str = ", ".join([f'"{rel_type}"' for rel_type in schema.get("relationship_types", [])])

        prompt = f"""
        You are an expert knowledge graph extractor. Your task is to analyze the text provided
        and extract entities and their relationships based on the provided schema.
        Return the result as a single, valid JSON object and nothing else.

        SCHEMA:
        - Allowed Entity Labels: [{node_labels_str}]
        - Allowed Relationship Types: [{rel_types_str}]

        GENERIC EXAMPLE:
        Text: "John Doe, a software engineer at Acme Corp, is leading the new 'Phoenix' project. He reports to Jane Smith."
        JSON:
        {{
            "entities": [
                {{"label": "Person", "name": "John Doe"}},
                {{"label": "Company", "name": "Acme Corp"}},
                {{"label": "Project", "name": "Phoenix"}},
                {{"label": "Person", "name": "Jane Smith"}}
            ],
            "relationships": [
                {{"source": "John Doe", "target": "Acme Corp", "type": "WORKS_AT"}},
                {{"source": "John Doe", "target": "Phoenix", "type": "LEADS"}},
                {{"source": "John Doe", "target": "Jane Smith", "type": "REPORTS_TO"}}
            ]
        }}

        Now, analyze the following text using the provided schema:
        Text: "{chunk_text}"
        JSON:
        """
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.llm_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                )
                await self._safe_raise_for_status(response)
                resp_json = response.json()
                if asyncio.iscoroutine(resp_json):
                    resp_json = await resp_json
                response_text = resp_json["response"]
                return json.loads(response_text)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Ollama for extraction: {e.response.status_code} - {e.response.text}")
            return {"entities": [], "relationships": []}
        except Exception as e:
            logger.error(f"Error calling Ollama for generic extraction: {e}")
            return {"entities": [], "relationships": []}

    def _save_knowledge_graph(self, chunk_id: str, extracted_data: Dict[str, Any]):
        """Save the extracted entities and relationships to Neo4j using APOC"""
        if self._db_disabled or not extracted_data: return

        query = """
        MATCH (c:Chunk {id: $chunk_id})
        UNWIND $entities AS entity_data
        CALL apoc.merge.node([entity_data.label], {name: entity_data.name}) YIELD node AS entity_node
        MERGE (c)-[:MENTIONS]->(entity_node)
        WITH c
        UNWIND $relationships AS rel_data
        MATCH (source {name: rel_data.source})
        MATCH (target {name: rel_data.target})
        CALL apoc.merge.relationship(source, rel_data.type, {}, {}, target) YIELD rel
        RETURN count(rel)
        """
        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    chunk_id=chunk_id,
                    entities=extracted_data.get("entities", []),
                    relationships=extracted_data.get("relationships", [])
                )
            logger.info(f"Saved knowledge graph entities/relationships from chunk {chunk_id}.")
        except Exception as e:
            logger.error(f"Error saving knowledge graph (ensure APOC plugin is installed): {e}")

    # --- Main Ingestion Pipeline ---

    async def ingest_from_content(self, content: str, filename: str, embedding_provider: str = None) -> Dict[str, Any]:
        try:
            logger.info(f"Starting GENERIC knowledge ingestion for {filename}")
            document_id = str(uuid.uuid4())
            
            # Check Ollama health
            ollama_healthy = await self._check_ollama_health()
            if not ollama_healthy:
                logger.warning("Ollama not available, continuing with document chunking only")
            
            # --- Schema Inference Phase ---
            content_sample = content[:4000]
            inferred_schema = await self._infer_graph_schema(content_sample)
            
            # --- Document Graph Phase ---
            self._ensure_vector_index()
            text_chunks = self._create_chunks(content)
            if not text_chunks:
                raise ValueError("No content to process after chunking")

            # Generate embeddings with fallback
            try:
                # Use provided embedding provider or fall back to settings
                selected_provider = embedding_provider or settings.embedding_provider
                embeddings = await self._generate_embeddings(text_chunks, provider=selected_provider)
            except Exception:
                logger.warning("Embedding generation failed; using zero vectors as fallback.")
                dim = getattr(settings, "openai_embedding_dimensions", 768)
                embeddings = [[0.0] * dim for _ in text_chunks]

            # Persist using helper (no-op in degraded mode)
            document_id = self._save_to_neo4j(text_chunks, embeddings, filename)

            # Reconstroi a lista de chunks para a fase de extração de conhecimento
            chunk_data_list = []
            for i, (chunk_text, embedding) in enumerate(zip(text_chunks, embeddings)):
                chunk_data_list.append({
                    "chunk_id": f"{document_id}-chunk-{i}",
                    "text": chunk_text,
                    "embedding": embedding,
                    "chunk_index": i,
                })
            
            # --- Knowledge Graph Phase (only if Ollama is the selected provider) ---
            if ollama_healthy and selected_provider == "ollama":
                logger.info("Starting knowledge extraction phase with inferred schema (Ollama provider)...")
                for chunk_data in chunk_data_list:
                    extracted_knowledge = await self._call_ollama_for_extraction(chunk_data["text"], inferred_schema)
                    if extracted_knowledge and (extracted_knowledge.get("entities") or extracted_knowledge.get("relationships")):
                        self._save_knowledge_graph(chunk_data["chunk_id"], extracted_knowledge)
            else:
                logger.warning(f"Skipping knowledge extraction phase. Reason: Ollama not healthy or provider is '{selected_provider}'.")

            logger.info(f"Generic knowledge ingestion completed for document {document_id}")
            return {
                "document_id": document_id, 
                "chunks_created": len(text_chunks),
                "filename": filename, 
                "status": "success", 
                "inferred_schema": inferred_schema,
                "ollama_available": ollama_healthy
            }
            
        except Exception as e:
            logger.error(f"Error during generic knowledge ingestion: {str(e)}")
            raise Exception(f"Generic ingestion failed: {str(e)}")

    async def ingest_from_file_upload(self, file_content: bytes, filename: str, embedding_provider: str = "ollama"):
        if not is_valid_file_type(filename):
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Usar factory para obter loader apropriado
        from .document_loaders import DocumentLoaderFactory
        loader = DocumentLoaderFactory.get_loader(filename, file_content)
        text_content = loader.extract_text()
        
        # Continuar com pipeline existente
        return await self.ingest_from_content(text_content, filename, embedding_provider)
    
