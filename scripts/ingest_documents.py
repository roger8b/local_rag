#!/usr/bin/env python3
"""
Script para ingestão de documentos no sistema RAG.
Carrega documentos .txt, divide em chunks, gera embeddings e salva no Neo4j.

Uso:
    python scripts/ingest_documents.py --file path/to/document.txt
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
from typing import List
import httpx
from neo4j import GraphDatabase
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Add src to Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings


class DocumentIngester:
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
        if self.driver:
            self.driver.close()
    
    def create_vector_index(self):
        """Create vector index for chunks if it doesn't exist"""
        with self.driver.session() as session:
            # Check if index exists
            result = session.run("SHOW INDEXES YIELD name WHERE name = 'chunks_vector_index'")
            if result.single():
                print("Vector index 'chunks_vector_index' already exists.")
                return
            
            # Create vector index
            query = """
            CREATE VECTOR INDEX chunks_vector_index IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: 768,
                    `vector.similarity_function`: 'cosine'
                }
            }
            """
            session.run(query)
            print("Created vector index 'chunks_vector_index'.")
    
    def load_document(self, file_path: str) -> str:
        """Load document using LangChain TextLoader"""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return documents[0].page_content
        except Exception as e:
            raise Exception(f"Error loading document {file_path}: {str(e)}")
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using RecursiveCharacterTextSplitter"""
        chunks = self.text_splitter.split_text(text)
        return chunks
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={
                        "model": settings.embedding_model,
                        "prompt": text
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["embedding"]
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")
    
    async def save_chunks_to_neo4j(self, chunks: List[str], source_file: str):
        """Save chunks with embeddings to Neo4j"""
        with self.driver.session() as session:
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}...")
                
                # Generate embedding
                embedding = await self.generate_embedding(chunk)
                
                # Save to Neo4j
                query = """
                CREATE (c:Chunk {
                    text: $text,
                    embedding: $embedding,
                    source_file: $source_file,
                    chunk_index: $chunk_index,
                    created_at: datetime()
                })
                """
                session.run(
                    query,
                    text=chunk,
                    embedding=embedding,
                    source_file=source_file,
                    chunk_index=i
                )
                
                print(f"Saved chunk {i+1} to Neo4j.")
    
    async def ingest_document(self, file_path: str):
        """Main ingestion method"""
        print(f"Starting ingestion of {file_path}...")
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create vector index
        self.create_vector_index()
        
        # Load document
        print("Loading document...")
        text = self.load_document(file_path)
        print(f"Loaded document with {len(text)} characters.")
        
        # Split into chunks
        print("Splitting text into chunks...")
        chunks = self.split_text(text)
        print(f"Created {len(chunks)} chunks.")
        
        # Save chunks to Neo4j
        print("Saving chunks to Neo4j...")
        await self.save_chunks_to_neo4j(chunks, os.path.basename(file_path))
        
        print(f"Successfully ingested {len(chunks)} chunks from {file_path}")


async def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into the RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ingest_documents.py --file document.txt
  python scripts/ingest_documents.py --file /path/to/document.txt
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the .txt file to ingest"
    )
    
    args = parser.parse_args()
    
    # Validate file extension
    if not args.file.endswith('.txt'):
        print("Error: Only .txt files are supported.")
        sys.exit(1)
    
    ingester = DocumentIngester()
    
    try:
        await ingester.ingest_document(args.file)
    except Exception as e:
        print(f"Error during ingestion: {str(e)}")
        sys.exit(1)
    finally:
        ingester.close()
    
    print("Ingestion completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())