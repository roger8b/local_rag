from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from src.models.api_models import QueryRequest, QueryResponse, ErrorResponse, IngestResponse
from src.retrieval.retriever import VectorRetriever
from src.generation.generator import ResponseGenerator
from src.application.services.ingestion_service import IngestionService, is_valid_file_type
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=201,
    summary="Ingerir documento via upload",
    operation_id="postIngest",
    tags=["ingest"],
    responses={
        201: {"model": IngestResponse, "description": "Document successfully ingested"},
        415: {"model": ErrorResponse, "description": "Unsupported Media Type"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
async def ingest_endpoint(file: UploadFile = File(...), embedding_provider: str = Form("ollama")):
    """
    Ingest a document file into the RAG system
    
    - **file**: Text file (.txt) to be processed and added to the knowledge base
    - **embedding_provider**: The embedding provider to use ('ollama' or 'openai')
    
    The file will be processed, split into chunks, embedded, and stored in Neo4j.
    """
    try:
        # Validate file type
        if not is_valid_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type. Only .txt files are supported. Received: {file.filename}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="File is empty"
            )
        
        # Initialize ingestion service
        ingestion_service = IngestionService()
        
        try:
            # Process the file
            result = await ingestion_service.ingest_from_file_upload(
                file_content, file.filename, embedding_provider=embedding_provider
            )
            
            return IngestResponse(
                status="success",
                filename=file.filename,
                document_id=result["document_id"],
                chunks_created=result["chunks_created"],
                message="Document successfully ingested and indexed"
            )
            
        finally:
            # Clean up resources
            ingestion_service.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Executa consulta RAG",
    operation_id="postQuery",
    tags=["query"],
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
