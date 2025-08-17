from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str = Field(..., description="The question to be answered", min_length=1)


class DocumentSource(BaseModel):
    text: str = Field(..., description="The text content of the chunk")
    score: float = Field(..., description="Similarity score of the chunk")


class QueryResponse(BaseModel):
    answer: str = Field(..., description="The generated answer from the LLM")
    sources: List[DocumentSource] = Field(..., description="List of document chunks used as sources")
    question: str = Field(..., description="The original question")


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if applicable")