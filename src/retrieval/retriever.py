import httpx
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.models.api_models import DocumentSource
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class VectorRetriever:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self._db_disabled = False
            logger.info("Neo4j connection established for retrieval.")
        except Exception as e:
            logger.error(f"Neo4j unavailable for retrieval: {e}")
            self.driver = None
            self._db_disabled = True
            
        # Cache para armazenar dimensões esperadas
        self._expected_dimensions = None
        
    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    async def _check_ollama_health(self) -> bool:
        """Verifica se Ollama está rodando"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.ollama_base_url}")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def _get_stored_embedding_dimensions(self) -> Optional[int]:
        """Verifica as dimensões dos embeddings armazenados no Neo4j"""
        if self._db_disabled:
            return None
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Chunk) 
                    WHERE c.embedding IS NOT NULL 
                    RETURN c.embedding as embedding
                    LIMIT 1
                """)
                
                record = result.single()
                if record and record["embedding"]:
                    dimensions = len(record["embedding"])
                    logger.info(f"Stored embeddings have {dimensions} dimensions")
                    return dimensions
                else:
                    logger.warning("No embeddings found in database")
                    return None
                    
        except Exception as e:
            logger.error(f"Error checking stored embedding dimensions: {e}")
            return None

    async def generate_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding for text using Ollama with proper endpoint and error handling
        """
        if not await self._check_ollama_health():
            raise Exception("Ollama service is not available")

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # CORREÇÃO 1: Endpoint correto /api/embed
                    response = await client.post(
                        f"{settings.ollama_base_url}/api/embed",
                        json={
                            # CORREÇÃO 2: Campo 'input' como lista, não 'prompt'
                            "model": settings.embedding_model,
                            "input": [text]  # Input deve ser uma lista
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # CORREÇÃO 3: Acessar embeddings[0], não embedding
                    if "embeddings" not in result:
                        raise ValueError("Invalid response from Ollama embed API")
                    
                    embeddings = result["embeddings"]
                    if not embeddings or len(embeddings) == 0:
                        raise ValueError("No embeddings returned from Ollama")
                    
                    embedding = embeddings[0]  # Primeiro (e único) embedding
                    
                    # VALIDAÇÃO: Verificar dimensões
                    current_dimensions = len(embedding)
                    
                    # Cache das dimensões esperadas
                    if self._expected_dimensions is None:
                        self._expected_dimensions = self._get_stored_embedding_dimensions()
                    
                    # Verificar compatibilidade de dimensões
                    if self._expected_dimensions and current_dimensions != self._expected_dimensions:
                        raise ValueError(
                            f"Embedding dimension mismatch: "
                            f"Generated {current_dimensions} dimensions, "
                            f"but stored embeddings have {self._expected_dimensions} dimensions. "
                            f"Model: {settings.embedding_model}"
                        )
                    
                    logger.info(f"Generated embedding with {current_dimensions} dimensions")
                    return embedding
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error generating embedding (attempt {attempt + 1}): "
                           f"{e.response.status_code} - {e.response.text}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate embedding after {max_retries} attempts: "
                                  f"HTTP {e.response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error generating embedding (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate embedding after {max_retries} attempts: {str(e)}")
                
                # Esperar antes de tentar novamente
                await asyncio.sleep(1 * (attempt + 1))

    def search_similar_chunks(self, embedding: List[float], top_k: int = 5) -> List[DocumentSource]:
        """Search for similar chunks in Neo4j using vector similarity"""
        if self._db_disabled:
            logger.warning("Neo4j disabled, returning empty results")
            return []
            
        try:
            with self.driver.session() as session:
                # Verificar se o índice existe
                index_check = session.run(
                    "SHOW INDEXES YIELD name WHERE name = 'document_embeddings'"
                )
                
                if not index_check.single():
                    raise Exception("Vector index 'document_embeddings' not found. "
                                  "Run ingestion first to create the index.")
                
                # Query vetorial
                query = """
                CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding) 
                YIELD node, score
                RETURN node.text as text, 
                       node.source_file as source_file,
                       node.chunk_index as chunk_index,
                       node.document_id as document_id,
                       score
                ORDER BY score DESC
                """
                
                result = session.run(query, embedding=embedding, top_k=top_k)
                
                sources = []
                for record in result:
                    sources.append(DocumentSource(
                        text=record["text"],
                        score=float(record["score"]),
                        # Campos adicionais opcionais (se o modelo suportar)
                        metadata={
                            "source_file": record.get("source_file"),
                            "chunk_index": record.get("chunk_index"),
                            "document_id": record.get("document_id")
                        }
                    ))
                
                logger.info(f"Retrieved {len(sources)} similar chunks")
                return sources
                
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            raise Exception(f"Vector search failed: {str(e)}")

    def search_text_chunks(self, question: str, top_k: int = 5) -> List[DocumentSource]:
        """Fallback: Search chunks using text similarity if vector search fails"""
        if self._db_disabled:
            return []
            
        try:
            with self.driver.session() as session:
                # Busca textual simples usando CONTAINS
                query = """
                MATCH (c:Chunk)
                WHERE toLower(c.text) CONTAINS toLower($question)
                RETURN c.text as text, 
                       c.source_file as source_file,
                       c.chunk_index as chunk_index,
                       1.0 as score
                ORDER BY c.chunk_index
                LIMIT $top_k
                """
                
                result = session.run(query, question=question, top_k=top_k)
                
                sources = []
                for record in result:
                    sources.append(DocumentSource(
                        text=record["text"],
                        score=float(record["score"])
                    ))
                
                logger.info(f"Text search returned {len(sources)} chunks")
                return sources
                
        except Exception as e:
            logger.error(f"Error during text search: {e}")
            return []

    async def retrieve(self, question: str, top_k: int = 5, fallback_to_text: bool = True) -> List[DocumentSource]:
        """
        Main retrieval method: generate embedding and search similar chunks
        with fallback to text search if vector search fails
        """
        try:
            # Primeiro tentar busca vetorial
            logger.info(f"Starting vector retrieval for question: {question[:100]}...")
            
            # Generate embedding for the question
            embedding = await self.generate_embedding(question)
            
            # Search for similar chunks
            sources = self.search_similar_chunks(embedding, top_k)
            
            if not sources and fallback_to_text:
                logger.warning("Vector search returned no results, falling back to text search")
                sources = self.search_text_chunks(question, top_k)
            
            logger.info(f"Retrieved {len(sources)} total sources")
            return sources
            
        except Exception as e:
            logger.error(f"Error during vector retrieval: {str(e)}")
            
            if fallback_to_text:
                logger.info("Attempting fallback to text search...")
                try:
                    sources = self.search_text_chunks(question, top_k)
                    if sources:
                        logger.info(f"Fallback search returned {len(sources)} sources")
                        return sources
                except Exception as fallback_error:
                    logger.error(f"Fallback search also failed: {fallback_error}")
            
            raise Exception(f"Error during retrieval: {str(e)}")

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna o status do sistema de retrieval"""
        status = {
            "neo4j_connected": not self._db_disabled,
            "expected_dimensions": self._expected_dimensions
        }
        
        if not self._db_disabled:
            try:
                with self.driver.session() as session:
                    # Contar chunks disponíveis
                    result = session.run("MATCH (c:Chunk) RETURN count(c) as total")
                    status["total_chunks"] = result.single()["total"]
                    
                    # Verificar índice vetorial
                    result = session.run(
                        "SHOW INDEXES YIELD name WHERE name = 'document_embeddings'"
                    )
                    status["vector_index_exists"] = result.single() is not None
                    
            except Exception as e:
                status["neo4j_error"] = str(e)
        
        return status

    async def health_check(self) -> Dict[str, Any]:
        """Verificação completa de saúde do sistema"""
        health = {
            "timestamp": "now",
            "ollama_healthy": await self._check_ollama_health(),
            "neo4j_healthy": not self._db_disabled,
            "system_status": self.get_system_status()
        }
        
        # Teste de embedding se Ollama estiver funcionando
        if health["ollama_healthy"]:
            try:
                test_embedding = await self.generate_embedding("test")
                health["embedding_test"] = {
                    "success": True,
                    "dimensions": len(test_embedding)
                }
            except Exception as e:
                health["embedding_test"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return health