from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    # Controla se devemos chamar verify_connectivity() na inicialização do driver
    neo4j_verify_connectivity: bool = True
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    llm_model: str = "qwen3:8b"
    embedding_dimension: int = 768
    embedding_batch_size: int = 32
    embedding_max_retries: int = 10

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    # Default embedding dimensions for OpenAI text-embedding-3 models
    openai_embedding_dimensions: int = 768
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Local RAG API"
    api_version: str = "v1"
    api_base_url: str = "http://localhost:8000"
    default_timeout: int = 120
    log_level: str = "INFO"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
