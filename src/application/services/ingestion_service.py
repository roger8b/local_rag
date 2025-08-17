"""
Ingestion service for processing documents and adding them to the knowledge base.
Refactored from scripts/ingest_documents.py to be reusable within the application.
"""

import asyncio
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
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
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
        with self.driver.session() as session:
            # Check if index exists
            result = session.run("SHOW INDEXES YIELD name WHERE name = 'document_embeddings'")
            if result.single():
                logger.info("Vector index 'document_embeddings' already exists.")
                return
            
            # Create vector index
            query = """
            CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }
            }
            """
            session.run(query)
            logger.info("Created vector index 'document_embeddings'.")
    
    def _create_chunks(self, content: str) -> List[str]:
        """Split content into chunks"""
        return self.text_splitter.split_text(content)
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for chunks using Ollama"""
        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for chunk in chunks:
                try:
                    response = await client.post(
                        f"{settings.ollama_base_url}/api/embeddings",
                        json={
                            "model": settings.embedding_model,
                            "prompt": chunk
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    embeddings.append(result["embedding"])
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk: {str(e)}")
                    raise Exception(f"Failed to generate embeddings: {str(e)}")
        return embeddings
    
    def _save_to_neo4j(self, chunks: List[str], embeddings: List[List[float]], filename: str) -> str:
        """Save chunks and embeddings to Neo4j"""
        document_id = str(uuid.uuid4())
        
        with self.driver.session() as session:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                query = """
                CREATE (c:Chunk {
                    id: $chunk_id,
                    text: $text,
                    embedding: $embedding,
                    source_file: $source_file,
                    document_id: $document_id,
                    chunk_index: $chunk_index,
                    created_at: datetime()
                })
                """
                chunk_id = f"{document_id}-chunk-{i}"
                session.run(
                    query,
                    chunk_id=chunk_id,
                    text=chunk,
                    embedding=embedding,
                    source_file=filename,
                    document_id=document_id,
                    chunk_index=i
                )
                logger.debug(f"Saved chunk {i+1}/{len(chunks)} to Neo4j")
        
        return document_id
    
    async def ingest_from_content(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Main ingestion method that processes content directly
        
        Args:
            content: Text content to ingest
            filename: Original filename for metadata
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            logger.info(f"Starting ingestion of content from {filename}")
            
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
    
    async def ingest_from_file_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Ingest document from uploaded file content
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            
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
            return await self.ingest_from_content(content, filename)
            
        except Exception as e:
            logger.error(f"Error during file upload ingestion: {str(e)}")
            raise