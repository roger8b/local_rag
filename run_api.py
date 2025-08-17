#!/usr/bin/env python3
"""
Script para executar a API do RAG.
"""

import uvicorn
from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info"
    )