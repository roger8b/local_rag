from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to be answered", min_length=1)
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Quais são os componentes principais do sistema RAG?"
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
