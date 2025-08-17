from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "qwen3:8b"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Local RAG API"
    api_version: str = "v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()