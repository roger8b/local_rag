from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import List, Optional, Literal, Union
from datetime import datetime


class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to be answered", min_length=1)
    provider: Optional[Literal["ollama", "openai", "gemini"]] = Field(
        None, 
        description="LLM provider to use for this query. If not specified, uses the default configured provider."
    )
    model_name: Optional[str] = Field(
        None,
        description="Optional specific model name to use within the chosen provider."
    )
    model_name: Optional[str] = Field(
        None,
        description="Specific model to use within the provider. If not specified, uses the default model for the provider."
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Quais são os componentes principais do sistema RAG?",
                "provider": "openai",
                "model_name": "gpt-4o-mini"
            }
        }
    )


class DocumentSource(BaseModel):
    text: str = Field(..., description="The text content of the chunk")
    score: float = Field(..., description="Similarity score of the chunk")
    metadata: Optional[dict] = Field(None, description="Source metadata")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "O sistema RAG usa um retriever baseado em vetores e um gerador LLM.",
                "score": 0.87,
                "metadata": {
                    "source_file": "doc.txt",
                    "chunk_index": 1
                }
            }
        }
    )


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from the LLM")
    sources: List[DocumentSource] = Field(..., description="List of document chunks used as sources")
    question: str = Field(..., description="The original question")
    provider_used: str = Field(..., description="The LLM provider that was used to generate this response")
    logs: Optional[List[dict]] = Field(None, description="Structured processing logs for UI rendering")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Os principais componentes são: (1) retriever vetorial para recuperar contextos relevantes, (2) gerador LLM para formular a resposta, e (3) storage/índice para persistência.",
                "sources": [
                    {
                        "text": "O sistema RAG usa um retriever baseado em vetores e um gerador LLM.",
                        "score": 0.87,
                    },
                    {
                        "text": "As fontes retornadas incluem os trechos mais relevantes do documento.",
                        "score": 0.82,
                    },
                ],
                "question": "Quais são os componentes principais do sistema RAG?",
                "provider_used": "openai"
            }
        }
    )


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "No relevant documents found for the given question",
                "error_code": "NOT_FOUND",
            }
        }
    )


class IngestResponse(BaseModel):
    status: str = Field(..., description="Status of the ingestion process")
    filename: str = Field(..., description="Name of the processed file")
    document_id: Optional[str] = Field(None, description="ID of the created document")
    chunks_created: Optional[int] = Field(None, description="Number of chunks created")
    message: Optional[str] = Field(None, description="Additional information")
    logs: Optional[List[dict]] = Field(None, description="Structured processing logs for UI rendering")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "filename": "documento_exemplo.txt",
                "document_id": "doc-abc123",
                "chunks_created": 3,
                "message": "Document successfully ingested and indexed"
            }
        }
    )


class SchemaInferRequest(BaseModel):
    text: str = Field(..., description="Text sample to analyze for schema inference", min_length=1)
    max_sample_length: Optional[int] = Field(
        500, 
        description="Maximum length of text to analyze (default: 500 characters)",
        ge=50,
        le=2000
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "João Silva trabalha na empresa TechCorp desde 2020. Ele é responsável pelo desenvolvimento de aplicações web utilizando React e Node.js. A TechCorp é uma startup de tecnologia focada em soluções de e-commerce.",
                "max_sample_length": 1000
            }
        }
    )


class SchemaInferResponse(BaseModel):
    node_labels: List[str] = Field(..., description="List of inferred node/entity types")
    relationship_types: List[str] = Field(..., description="List of inferred relationship types")
    source: Literal["llm", "fallback"] = Field(..., description="Source of the schema inference")
    model_used: Optional[str] = Field(None, description="LLM model used for inference (if applicable)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    reason: Optional[str] = Field(None, description="Reason for fallback (if applicable)")
    document_info: Optional[dict] = Field(None, description="Information about the source document (if from cache)")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_labels": ["Person", "Company", "Technology", "Role", "Industry"],
                "relationship_types": ["WORKS_AT", "RESPONSIBLE_FOR", "USES", "FOUNDED_IN", "FOCUSES_ON"],
                "source": "llm",
                "model_used": "qwen3:8b",
                "processing_time_ms": 1250.5,
                "reason": None,
                "document_info": {
                    "filename": "document.pdf",
                    "text_length": 15847,
                    "sample_used": 1000
                }
            }
        }
    )


class TextStats(BaseModel):
    total_chars: int = Field(..., description="Total number of characters in extracted text")
    total_words: int = Field(..., description="Total number of words in extracted text")
    total_lines: int = Field(..., description="Total number of lines in extracted text")


class SchemaUploadResponse(BaseModel):
    key: str = Field(..., description="Unique key to reference the uploaded document")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    text_stats: TextStats = Field(..., description="Statistics about the extracted text")
    processing_time_ms: float = Field(..., description="Time taken to process the upload in milliseconds")
    created_at: datetime = Field(..., description="Upload timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    file_type: str = Field(..., description="Detected file type (txt, pdf)")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.pdf",
                "file_size_bytes": 1048576,
                "text_stats": {
                    "total_chars": 15847,
                    "total_words": 2341,
                    "total_lines": 156
                },
                "processing_time_ms": 234.5,
                "created_at": "2025-01-15T10:30:00Z",
                "expires_at": "2025-01-15T11:00:00Z",
                "file_type": "pdf"
            }
        }
    )


class SchemaInferByKeyRequest(BaseModel):
    document_key: Optional[str] = Field(None, description="Key of uploaded document to analyze")
    text: Optional[str] = Field(None, description="Direct text to analyze (alternative to document_key)", min_length=1)
    sample_percentage: Optional[int] = Field(
        50, 
        description="Percentage of text to analyze (0-100, default: 50%)",
        ge=0,
        le=100
    )
    max_sample_length: Optional[int] = Field(
        None, 
        description="Maximum length of text to analyze in characters (overrides sample_percentage if provided)",
        ge=50,
        le=2000
    )
    llm_provider: Optional[Literal["ollama", "openai", "gemini"]] = Field(
        None, 
        description="LLM provider to use for inference (overrides default)"
    )
    llm_model: Optional[str] = Field(
        None,
        description="Specific model name to use within the provider"
    )
    
    @classmethod
    def model_validate(cls, value):
        """Custom validation to handle empty text properly"""
        if isinstance(value, dict):
            # If text is provided but empty, let validation handle it
            if "text" in value and value["text"] == "":
                # This will trigger the min_length=1 validation
                pass
        return super().model_validate(value)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_key": "550e8400-e29b-41d4-a716-446655440000",
                "sample_percentage": 30,
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini"
            }
        }
    )


class DocumentCacheInfo(BaseModel):
    key: str = Field(..., description="Document key")
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size in bytes")
    text_stats: TextStats = Field(..., description="Statistics about the extracted text")
    created_at: datetime = Field(..., description="Upload timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    last_accessed: datetime = Field(..., description="Last access timestamp")


class DocumentCacheListResponse(BaseModel):
    documents: List[DocumentCacheInfo] = Field(..., description="List of cached documents")
    total_documents: int = Field(..., description="Total number of cached documents")
    memory_usage_mb: float = Field(..., description="Current memory usage in MB")
    total_file_size_mb: float = Field(..., description="Total file size in MB")
    max_documents: int = Field(..., description="Maximum allowed documents in cache")
    ttl_minutes: int = Field(..., description="Time to live in minutes")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "documents": [
                    {
                        "key": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "document.pdf",
                        "file_size_bytes": 1048576,
                        "text_stats": {
                            "total_chars": 15847,
                            "total_words": 2341,
                            "total_lines": 156
                        },
                        "created_at": "2025-01-15T10:30:00Z",
                        "expires_at": "2025-01-15T11:00:00Z",
                        "last_accessed": "2025-01-15T10:35:00Z"
                    }
                ],
                "total_documents": 1,
                "memory_usage_mb": 15.2,
                "total_file_size_mb": 1.0,
                "max_documents": 100,
                "ttl_minutes": 30
            }
        }
    )


class DocumentRemoveResponse(BaseModel):
    message: str = Field(..., description="Success message")
    key: str = Field(..., description="Key of removed document")
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Document removed successfully",
                "key": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )
