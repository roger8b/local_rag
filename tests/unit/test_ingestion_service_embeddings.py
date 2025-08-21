import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.application.services.ingestion_service import IngestionService


@pytest.mark.asyncio
async def test_generate_embeddings_openai_without_api_key(monkeypatch):
    svc = IngestionService()
    # Force provider openai and missing key
    with patch("src.application.services.ingestion_service.settings") as mock_settings:
        mock_settings.openai_api_key = None
        mock_settings.openai_embedding_model = "text-embedding-3-small"
        mock_settings.openai_embedding_dimensions = 1536
        with pytest.raises(ValueError):
            await svc._generate_embeddings(["a", "b"], provider="openai")


@pytest.mark.asyncio
async def test_generate_embeddings_ollama_missing_key_in_response(monkeypatch):
    svc = IngestionService()
    # Mock AsyncClient to return payload missing 'embeddings'
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"oops": []}

    async_client = MagicMock()
    async_client.post = AsyncMock(return_value=_Resp())

    class _ClientCtx:
        async def __aenter__(self):
            return async_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("src.application.services.ingestion_service.httpx.AsyncClient", return_value=_ClientCtx()):
        with pytest.raises(ValueError):
            await svc._generate_embeddings(["chunk"], provider="ollama")


@pytest.mark.asyncio
async def test_generate_embeddings_count_mismatch(monkeypatch):
    svc = IngestionService()

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [[0.1, 0.2]]}  # only one embedding

    async_client = MagicMock()
    async_client.post = AsyncMock(return_value=_Resp())

    class _ClientCtx:
        async def __aenter__(self):
            return async_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("src.application.services.ingestion_service.httpx.AsyncClient", return_value=_ClientCtx()):
        with pytest.raises(ValueError):
            await svc._generate_embeddings(["c1", "c2"], provider="ollama")


@pytest.mark.asyncio
async def test_ingest_from_content_fallback_zero_vectors(monkeypatch):
    svc = IngestionService()

    # Make chunking deterministic
    monkeypatch.setattr(svc, "_create_chunks", lambda content: ["x", "y", "z"])
    # Simulate Ollama not available to skip extraction phase
    monkeypatch.setattr(svc, "_check_ollama_health", AsyncMock(return_value=False))
    # Ensure vector index step no-ops
    monkeypatch.setattr(svc, "_ensure_vector_index", lambda: None)
    # Fail embedding generation to force fallback
    async def _raise(*args, **kwargs):
        raise Exception("embed failed")

    monkeypatch.setattr(svc, "_generate_embeddings", _raise)
    # Bypass DB persistence
    monkeypatch.setattr(svc, "_save_to_neo4j", lambda chunks, embs, fn: "doc-1")

    result = await svc.ingest_from_content("abc", "file.txt")
    assert result["status"] == "success"
    assert result["chunks_created"] == 3
