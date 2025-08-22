from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import List, Optional, Literal


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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "O sistema RAG usa um retriever baseado em vetores e um gerador LLM.",
                "score": 0.87,
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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "node_labels": ["Person", "Company", "Technology", "Role", "Industry"],
                "relationship_types": ["WORKS_AT", "RESPONSIBLE_FOR", "USES", "FOUNDED_IN", "FOCUSES_ON"],
                "source": "llm",
                "model_used": "qwen3:8b",
                "processing_time_ms": 1250.5,
                "reason": None
            }
        }
    )
