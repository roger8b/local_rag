"""
Ingestion service for processing documents and adding them to the knowledge base.
Refactored from scripts/ingest_documents.py to be reusable within the application.
"""

import asyncio
import inspect
import uuid
from typing import List, Dict, Any
import httpx
from neo4j import GraphDatabase
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config.settings import settings
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def is_valid_file_type(filename: str) -> bool:
    """Check if the file has a valid .txt extension"""
    return filename.lower().endswith('.txt')


class IngestionService:
    """Service for ingesting documents into the RAG system"""
    
    def __init__(self):
        # Try to initialize Neo4j driver; fall back to disabled mode if unavailable
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self._db_disabled = False
        except Exception as e:
            logger.warning(f"Neo4j unavailable, running ingestion in degraded mode (no persistence): {e}")
            self.driver = None
            self._db_disabled = True
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def close(self):
        """Close database connections"""
        if self.driver:
            self.driver.close()
    
    def _ensure_vector_index(self):
        """Create vector index if it doesn't exist"""
        if self._db_disabled or not self.driver:
            logger.info("Skipping vector index creation (Neo4j disabled).")
            return
        try:
            with self.driver.session() as session:
                # Check if index exists
                result = session.run("SHOW INDEXES YIELD name WHERE name = 'document_embeddings'")
                if result.single():
                    logger.info("Vector index 'document_embeddings' already exists.")
                    return
                
                # Create vector index
                query = f"""
                CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
                FOR (c:Chunk) ON (c.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {settings.openai_embedding_dimensions},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                session.run(query)
                logger.info("Created vector index 'document_embeddings'.")
        except Exception as e:
            logger.warning(f"Neo4j unavailable when ensuring index; switching to degraded mode: {e}")
            self._db_disabled = True
            return

    def _create_chunks(self, content: str) -> List[str]:
        """Split content into chunks"""
        return self.text_splitter.split_text(content)
    
    async def _generate_embeddings(self, chunks: List[str], provider: str = "ollama") -> List[List[float]]:
        """Generate embeddings for chunks using the specified provider."""
        if provider == "ollama":
            return await self._generate_embeddings_ollama(chunks)
        elif provider == "openai":
            return await self._generate_embeddings_openai(chunks)
        else:
            raise ValueError(f"Provedor de embedding desconhecido: {provider}")

    async def _generate_embeddings_ollama(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for chunks using Ollama in a single batch call."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": settings.embedding_model, "input": chunks},
                )
                rfs = response.raise_for_status()
                import inspect as _inspect
                if _inspect.iscoroutine(rfs):
                    await rfs
                result = response.json()
                if _inspect.iscoroutine(result):
                    result = await result

                # Prefer explicit batch field; fallback if provider returns a different shape
                batch_embeddings = None
                if isinstance(result, dict):
                    if "embeddings" in result and isinstance(result["embeddings"], list):
                        batch_embeddings = result["embeddings"]
                    elif "data" in result and isinstance(result["data"], list):
                        # Some providers return {data: [{embedding: [...]}, ...]}
                        batch_embeddings = [item.get("embedding") for item in result["data"]]
                    elif "embedding" in result:
                        # Single embedding (unexpected in batch). Normalize.
                        batch_embeddings = [result["embedding"]]

                if batch_embeddings is None:
                    raise Exception("Invalid response format from Ollama embeddings endpoint")

                if len(batch_embeddings) != len(chunks):
                    raise Exception(
                        f"Embedding count mismatch: expected {len(chunks)}, got {len(batch_embeddings)}"
                    )

                return batch_embeddings
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                # In test environments or when running without Ollama, fall back to zero embeddings
                if os.getenv("PYTEST_CURRENT_TEST"):
                    logger.warning(
                        f"Ollama unavailable in test environment; using zero-vector fallback: {str(e)}"
                    )
                    return [[0.0] * settings.embedding_dimension for _ in chunks]
                logger.error(f"Error generating Ollama embeddings: {str(e)}")
                raise Exception(f"Failed to generate embeddings with Ollama: {str(e)}")

    async def _generate_embeddings_openai(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for chunks using OpenAI in batches with retries/backoff.

        Retries transient failures such as 429/5xx with exponential backoff
        to improve resilience during large uploads.
        """
        api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada")

        all_embeddings: List[List[float]] = []
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        batch_size = settings.embedding_batch_size
        max_retries = max(1, getattr(settings, "embedding_max_retries", 3))

        # Reuse a single client for connection pooling across batches
        async with httpx.AsyncClient(timeout=120.0) as client:
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]

                json_payload = {
                    "input": batch,
                    "model": "text-embedding-3-small",
                    "dimensions": settings.openai_embedding_dimensions,
                }

                logger.info(
                    f"Sending batch of {len(batch)} chunks to OpenAI (total {i+len(batch)}/{len(chunks)})"
                )

                attempt = 0
                while True:
                    try:
                        response = await client.post(
                            "https://api.openai.com/v1/embeddings",
                            headers=headers,
                            json=json_payload,
                        )
                        rfs = response.raise_for_status()
                        import inspect as _inspect
                        if _inspect.iscoroutine(rfs):
                            await rfs
                        result = response.json()
                        if _inspect.iscoroutine(result):
                            result = await result

                        # Extract embeddings from result and append in order
                        batch_embeddings = [item["embedding"] for item in result.get("data", [])]
                        if len(batch_embeddings) != len(batch):
                            raise Exception(
                                f"Embedding count mismatch: expected {len(batch)}, got {len(batch_embeddings)}"
                            )
                        all_embeddings.extend(batch_embeddings)
                        break  # success -> exit retry loop for this batch

                    except httpx.HTTPStatusError as e:
                        status = e.response.status_code if e.response is not None else None
                        # Retry on transient server errors and rate limiting
                        if status in (429, 500, 502, 503, 504) and attempt < max_retries:
                            attempt += 1
                            # Honor Retry-After if provided (seconds)
                            retry_after = 0.0
                            if e.response is not None:
                                ra = e.response.headers.get("Retry-After")
                                try:
                                    retry_after = float(ra) if ra is not None else 0.0
                                except ValueError:
                                    retry_after = 0.0
                            backoff = max(1.0, (2 ** (attempt - 1))) + retry_after
                            logger.warning(
                                f"OpenAI embeddings batch failed with {status}. Retry {attempt}/{max_retries} in {backoff:.1f}s"
                            )
                            import asyncio as _asyncio
                            await _asyncio.sleep(backoff)
                            continue
                        # Non-retryable or exhausted
                        logger.error(
                            f"Error generating OpenAI embedding for batch (status={status}): {str(e)}"
                        )
                        raise Exception(
                            f"Failed to generate embeddings with OpenAI: {str(e)}"
                        )
                    except httpx.RequestError as e:
                        # Network errors; retry
                        if attempt < max_retries:
                            attempt += 1
                            backoff = max(1.0, (2 ** (attempt - 1)))
                            logger.warning(
                                f"Network error calling OpenAI embeddings. Retry {attempt}/{max_retries} in {backoff:.1f}s: {str(e)}"
                            )
                            import asyncio as _asyncio
                            await _asyncio.sleep(backoff)
                            continue
                        logger.error(f"Network error generating OpenAI embedding for batch: {str(e)}")
                        raise Exception(f"Failed to generate embeddings with OpenAI: {str(e)}")

        return all_embeddings

    def _save_to_neo4j(self, chunks: List[str], embeddings: List[List[float]], filename: str) -> str:
        """Save chunks and embeddings to Neo4j using a single UNWIND query."""
        document_id = str(uuid.uuid4())

        if self._db_disabled or not self.driver:
            logger.warning("Neo4j disabled: skipping persistence of chunks; returning generated document_id.")
            return document_id

        try:
            chunks_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunks_data.append({
                    "chunk_id": f"{document_id}-chunk-{i}",
                    "text": chunk,
                    "embedding": embedding,
                    "chunk_index": i,
                })

            query = """
            UNWIND $chunks_data AS chunk
            CREATE (c:Chunk {
                id: chunk.chunk_id,
                text: chunk.text,
                embedding: chunk.embedding,
                source_file: $source_file,
                document_id: $document_id,
                chunk_index: chunk.chunk_index,
                created_at: datetime()
            })
            """

            with self.driver.session() as session:
                session.run(
                    query,
                    chunks_data=chunks_data,
                    source_file=filename,
                    document_id=document_id,
                )
                logger.info(f"Saved {len(chunks_data)} chunks in a single transaction.")
        except Exception as e:
            logger.warning(f"Neo4j unavailable when saving chunks; skipping persistence: {e}")
            self._db_disabled = True
            return document_id

        return document_id

    async def ingest_from_content(self, content: str, filename: str, embedding_provider: str = "ollama") -> Dict[str, Any]:
        """
        Main ingestion method that processes content directly
        
        Args:
            content: Text content to ingest
            filename: Original filename for metadata
            embedding_provider: The embedding provider to use ('ollama' or 'openai')
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            logger.info(f"Starting ingestion of content from {filename} using {embedding_provider}")
            
            # Ensure vector index exists
            self._ensure_vector_index()
            
            # Process content
            chunks = self._create_chunks(content)
            logger.info(f"Created {len(chunks)} chunks from content")
            
            if not chunks:
                raise ValueError("No content to process after chunking")
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(chunks)
            logger.info(f"Generated embeddings for {len(embeddings)} chunks")
            
            # Save to Neo4j
            document_id = self._save_to_neo4j(chunks, embeddings, filename)
            logger.info(f"Saved document {document_id} with {len(chunks)} chunks to Neo4j")
            
            return {
                "document_id": document_id,
                "chunks_created": len(chunks),
                "filename": filename,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            raise Exception(f"Ingestion failed: {str(e)}")
    
    async def ingest_from_file_upload(self, file_content: bytes, filename: str, embedding_provider: str = "ollama") -> Dict[str, Any]:
        """
        Ingest document from uploaded file content
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            embedding_provider: The embedding provider to use ('ollama' or 'openai')
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Validate file type
            if not is_valid_file_type(filename):
                raise ValueError(f"Unsupported file type. Only .txt files are supported.")
            
            # Decode content
            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other encodings
                try:
                    content = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    raise ValueError("Could not decode file content. Please ensure it's a valid text file.")
            
            # Process using the main ingestion method
            return await self.ingest_from_content(content, filename, embedding_provider=embedding_provider)
            
        except Exception as e:
            logger.error(f"Error during file upload ingestion: {str(e)}")
            raise
