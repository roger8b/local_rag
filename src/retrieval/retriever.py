import httpx
from neo4j import GraphDatabase
from typing import List, Dict, Any
from src.config.settings import settings
from src.models.api_models import DocumentSource
import json


class VectorRetriever:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        
    def close(self):
        if self.driver:
            self.driver.close()
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={
                    "model": settings.embedding_model,
                    "prompt": text
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
    
    def search_similar_chunks(self, embedding: List[float], top_k: int = 5) -> List[DocumentSource]:
        """Search for similar chunks in Neo4j using vector similarity"""
        with self.driver.session() as session:
            query = """
            CALL db.index.vector.queryNodes('document_embeddings', $top_k, $embedding) 
            YIELD node, score
            RETURN node.text as text, score
            ORDER BY score DESC
            """
            
            result = session.run(query, embedding=embedding, top_k=top_k)
            
            sources = []
            for record in result:
                sources.append(DocumentSource(
                    text=record["text"],
                    score=float(record["score"])
                ))
            
            return sources
    
    async def retrieve(self, question: str, top_k: int = 5) -> List[DocumentSource]:
        """Main retrieval method: generate embedding and search similar chunks"""
        try:
            # Generate embedding for the question
            embedding = await self.generate_embedding(question)
            
            # Search for similar chunks
            sources = self.search_similar_chunks(embedding, top_k)
            
            return sources
            
        except Exception as e:
            raise Exception(f"Error during retrieval: {str(e)}")