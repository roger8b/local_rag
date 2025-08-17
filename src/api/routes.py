from fastapi import APIRouter, HTTPException, status
from src.models.api_models import QueryRequest, QueryResponse, ErrorResponse
from src.retrieval.retriever import VectorRetriever
from src.generation.generator import ResponseGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["query"])


@router.post(
    
    "/query",
    response_model=QueryResponse,
    summary="Executa consulta RAG",
    operation_id="postQuery",
    responses={
        200: {
            "description": "Resposta gerada com sucesso",
            "content": {
                "application/json": {
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
            },
        },
        404: {"model": ErrorResponse, "description": "No relevant documents found"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def query_endpoint(request: QueryRequest):
    """
    Query endpoint for RAG (Retrieval-Augmented Generation)
    
    - **question**: The question to be answered (required)
    
    Returns the generated answer along with the source documents used.
    """
    try:
        # Initialize retriever and generator
        retriever = VectorRetriever()
        generator = ResponseGenerator()
        
        try:
            # Retrieve relevant documents
            sources = await retriever.retrieve(request.question)
            
            if not sources:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant documents found for the given question"
                )
            
            # Generate response
            answer = await generator.generate_response(request.question, sources)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                question=request.question
            )
            
        finally:
            # Clean up resources
            retriever.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
