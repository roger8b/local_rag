from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.config.settings import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAPI/Swagger tags metadata
tags_metadata = [
    {
        "name": "query",
        "description": "Endpoints para consulta RAG (recuperação + geração). Envie uma pergunta e receba uma resposta com as fontes.",
    },
    {
        "name": "ingest",
        "description": "Endpoints para ingestão de documentos. Faça upload de arquivos .txt para adicionar à base de conhecimento.",
    },
    {
        "name": "health",
        "description": "Endpoints de verificação de saúde e status da API.",
    },
]

# Create FastAPI app with Swagger/Redoc enabled
app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    description="Local RAG API for document-based question answering",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "displayRequestDuration": True,
    },
    contact={
        "name": "Local RAG Maintainers",
        "email": "roger.8b@gmail.com",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=tags_metadata,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/", tags=["health"], summary="Status da API")
async def root():
    """Health check endpoint"""
    return {"message": "Local RAG API is running", "version": "1.0.0"}


@app.get("/health", tags=["health"], summary="Health check")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
