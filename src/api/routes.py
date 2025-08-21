from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Optional
from src.models.api_models import QueryRequest, QueryResponse, ErrorResponse, IngestResponse
from src.retrieval.retriever import VectorRetriever
from src.generation.generator import ResponseGenerator
from src.application.services.ingestion_service import IngestionService, is_valid_file_type
from src.config.settings import settings
import logging
import httpx
from neo4j import GraphDatabase

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
async def ingest_endpoint(
    file: UploadFile = File(...),
    embedding_provider: str = Form("ollama"),
    model_name: Optional[str] = Form(None)
):
    """
    Ingest a document file into the RAG system
    
    - **file**: Text file (.txt) or PDF file (.pdf) to be processed and added to the knowledge base
    - **embedding_provider**: Provider for embeddings ("ollama" or "openai", default: "ollama")
    - **model_name**: Specific model to use within the provider (optional, uses provider default if not specified)
    
    The file will be processed, split into chunks, embedded using the selected provider and model, and stored in Neo4j.
    """
    try:
        # Validate embedding provider
        valid_providers = ["ollama", "openai"]
        if embedding_provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid embedding provider: {embedding_provider}. Must be one of: {valid_providers}"
            )
        
        # Validate file type
        if not is_valid_file_type(file.filename):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file.filename}. Only .txt and .pdf files are supported."
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
                file_content, file.filename, embedding_provider, model_name
            )
            
            return IngestResponse(
                status="success",
                filename=file.filename,
                document_id=result["document_id"],
                chunks_created=result["chunks_created"],
                message="Document successfully ingested and indexed",
                logs=result.get("logs")
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
    - **provider**: Optional LLM provider to use ("ollama", "openai", "gemini"). If not specified, uses default from settings.
    - **model_name**: Optional specific model to use within the provider. If not specified, uses provider default.
    
    Returns the generated answer along with the source documents used and the provider that was used.
    """
    try:
        # Initialize retriever and generator with optional provider override
        retriever = VectorRetriever()
        generator = ResponseGenerator(provider_override=request.provider)
        
        try:
            import time
            logs: list[dict] = []
            t0 = time.perf_counter()
            # Retrieve relevant documents
            t_ret = time.perf_counter()
            sources = await retriever.retrieve(request.question)
            logs.append({"level": "info", "message": f"Busca vetorial retornou {len(sources)} fontes.", "duration_ms": round((time.perf_counter()-t_ret)*1000, 2)})
            
            if not sources:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No relevant documents found for the given question"
                )
            
            # Generate response
            t_gen = time.perf_counter()
            answer = await generator.generate_response(request.question, sources)
            logs.append({"level": "info", "message": f"Resposta gerada por '{generator.get_provider_name()}'.", "duration_ms": round((time.perf_counter()-t_gen)*1000, 2)})
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                question=request.question,
                provider_used=generator.get_provider_name(),
                logs=logs + [{"level": "success", "message": f"Consulta concluída em {round((time.perf_counter()-t0), 2)}s."}]
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


@router.get(
    "/models/{provider}",
    summary="Lista modelos disponíveis por provider",
    operation_id="getModels",
    tags=["models"],
    responses={
        200: {
            "description": "Lista de modelos disponíveis",
            "content": {
                "application/json": {
                    "example": {
                        "models": ["qwen3:8b", "llama2:13b"],
                        "default": "qwen3:8b"
                    }
                }
            }
        },
        422: {"model": ErrorResponse, "description": "Invalid provider"},
        503: {"model": ErrorResponse, "description": "Provider service unavailable"}
    }
)
async def get_models_endpoint(provider: str):
    """
    Get list of available models for a specific provider
    
    - **provider**: LLM provider ("ollama", "openai", "gemini")
    
    Returns a list of available models and the default model for the provider.
    """
    try:
        # Validate provider
        valid_providers = ["ollama", "openai", "gemini"]
        if provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid provider: {provider}. Must be one of: {valid_providers}"
            )
        
        if provider == "ollama":
            return await _get_ollama_models()
        elif provider == "openai":
            return _get_openai_models()
        elif provider == "gemini":
            return _get_gemini_models()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching models for {provider}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def _get_ollama_models():
    """Fetch models from Ollama API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            models = [model["name"] for model in data.get("models", [])]
            
            return {
                "models": models,
                "default": settings.ollama_default_model
            }
            
    except Exception as e:
        logger.warning(f"Ollama API unavailable: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama service is unavailable. Please check if Ollama is running."
        )


def _get_openai_models():
    """Return static list of OpenAI models"""
    return {
        "models": [
            "gpt-4o-mini",
            "gpt-4o", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "default": settings.openai_default_model
    }


def _get_gemini_models():
    """Return static list of Gemini models"""
    return {
        "models": [
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ],
        "default": settings.gemini_default_model
    }


@router.get(
    "/documents",
    summary="Lista documentos ingeridos",
    tags=["documents"],
)
async def list_documents():
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            result = session.run(
                """
                MATCH (d:Document)
                RETURN d.doc_id as doc_id, d.filename as filename, d.filetype as filetype, d.ingested_at as ingested_at
                ORDER BY d.ingested_at DESC
                """
            )
            docs = [
                {
                    "doc_id": r["doc_id"],
                    "filename": r["filename"],
                    "filetype": r["filetype"],
                    "ingested_at": r["ingested_at"],
                }
                for r in result
            ]
            return docs
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/documents/{doc_id}",
    summary="Remove documento e seus chunks",
    tags=["documents"],
)
async def delete_document(doc_id: str):
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            session.run(
                """
                MATCH (d:Document {doc_id: $doc_id})
                OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
                DETACH DELETE d, c
                """,
                doc_id=doc_id,
            )
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/db/status",
    summary="Status do banco de dados",
    tags=["db"],
)
async def db_status():
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            # Count documents and chunks
            docs = session.run("MATCH (d:Document) RETURN count(d) as total").single()["total"]
            chunks = session.run("MATCH (c:Chunk) RETURN count(c) as total").single()["total"]
            idx = session.run("SHOW INDEXES YIELD name WHERE name = 'document_embeddings'")
            vector_index_exists = idx.single() is not None
            return {
                "documents": docs,
                "chunks": chunks,
                "vector_index_exists": vector_index_exists,
            }
    except Exception as e:
        logger.error(f"Error fetching DB status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/db/reindex",
    summary="(Re)cria o índice vetorial",
    tags=["db"],
)
async def db_reindex():
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            query = f"""
            CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {{ indexConfig: {{
                `vector.dimensions`: {settings.openai_embedding_dimensions},
                `vector.similarity_function`: 'cosine'
            }}}}
            """
            session.run(query)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error creating vector index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/db/clear",
    summary="Limpa dados de desenvolvimento",
    tags=["db"],
)
async def db_clear(confirm: Optional[bool] = False):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation 'confirm=true' is required")
    try:
        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        with driver.session() as session:
            session.run("DROP INDEX document_embeddings IF EXISTS")
            session.run("MATCH (n:Chunk) DETACH DELETE n")
        return {"status": "cleared"}
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
