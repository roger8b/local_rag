import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.retrieval.retriever import VectorRetriever
from src.models.api_models import DocumentSource


@pytest.mark.asyncio
async def test_generate_embedding_success(monkeypatch):
    # Patch Neo4j driver to avoid real connection
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()

        retriever = VectorRetriever()

    # Health check returns True
    monkeypatch.setattr(retriever, "_check_ollama_health", AsyncMock(return_value=True))
    # No stored dimension constraint
    monkeypatch.setattr(retriever, "_get_stored_embedding_dimensions", lambda: None)

    # Mock httpx.AsyncClient post -> embeddings
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [[0.1, 0.2]]}

    async_client = MagicMock()
    async_client.post = AsyncMock(return_value=_Resp())

    class _ClientCtx:
        async def __aenter__(self):
            return async_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("src.retrieval.retriever.httpx.AsyncClient", return_value=_ClientCtx()):
        emb = await retriever.generate_embedding("hello")
        assert isinstance(emb, list)
        assert len(emb) == 2


@pytest.mark.asyncio
async def test_generate_embedding_invalid_response(monkeypatch):
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()
        retriever = VectorRetriever()

    monkeypatch.setattr(retriever, "_check_ollama_health", AsyncMock(return_value=True))
    monkeypatch.setattr(retriever, "_get_stored_embedding_dimensions", lambda: None)

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"not_embeddings": []}

    async_client = MagicMock()
    async_client.post = AsyncMock(return_value=_Resp())

    class _ClientCtx:
        async def __aenter__(self):
            return async_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("src.retrieval.retriever.httpx.AsyncClient", return_value=_ClientCtx()):
        # A função faz retry e no final encapsula como Exception genérica
        with pytest.raises(Exception):
            await retriever.generate_embedding("hello")


@pytest.mark.asyncio
async def test_generate_embedding_dimension_mismatch(monkeypatch):
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()
        retriever = VectorRetriever()

    monkeypatch.setattr(retriever, "_check_ollama_health", AsyncMock(return_value=True))
    monkeypatch.setattr(retriever, "_get_stored_embedding_dimensions", lambda: 3)

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [[0.1, 0.2]]}

    async_client = MagicMock()
    async_client.post = AsyncMock(return_value=_Resp())

    class _ClientCtx:
        async def __aenter__(self):
            return async_client

        async def __aexit__(self, exc_type, exc, tb):
            return False

    with patch("src.retrieval.retriever.httpx.AsyncClient", return_value=_ClientCtx()):
        # A função faz retry e no final encapsula como Exception genérica
        with pytest.raises(Exception):
            await retriever.generate_embedding("hello")


@pytest.mark.asyncio
async def test_retrieve_uses_fallback_when_no_vector_results(monkeypatch):
    # Avoid Neo4j
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()
        retriever = VectorRetriever()

    # Patch methods to isolate logic
    monkeypatch.setattr(retriever, "generate_embedding", AsyncMock(return_value=[0.1, 0.2]))
    monkeypatch.setattr(retriever, "search_similar_chunks", lambda emb, top_k=5: [])

    expected = [DocumentSource(text="fallback", score=1.0)]
    monkeypatch.setattr(retriever, "search_text_chunks", lambda q, top_k=5: expected)

    results = await retriever.retrieve("question", top_k=5)
    assert results == expected


def test_get_system_status_when_neo4j_disabled():
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.side_effect = Exception("no neo4j")
        retriever = VectorRetriever()
    status = retriever.get_system_status()
    assert status.get("neo4j_connected") is False


@pytest.mark.asyncio
async def test_health_check_all_healthy(monkeypatch):
    """
    Test health check when all services are running
    """
    with patch("src.retrieval.retriever.GraphDatabase.driver") as mock_driver:
        mock_driver.return_value = MagicMock()
        retriever = VectorRetriever()

    # Mock Ollama health
    monkeypatch.setattr(retriever, "_check_ollama_health", AsyncMock(return_value=True))

    # Mock embedding generation
    monkeypatch.setattr(retriever, "generate_embedding", AsyncMock(return_value=[0.1] * 10))

    # Mock Neo4j status
    monkeypatch.setattr(retriever, "get_system_status", lambda: {
        "neo4j_connected": True,
        "total_chunks": 100,
        "vector_index_exists": True
    })

    health = await retriever.health_check()

    assert health["ollama_healthy"] is True
    assert health["neo4j_healthy"] is True
    assert health["embedding_test"]["success"] is True
    assert health["system_status"]["total_chunks"] == 100


def test_search_similar_chunks_success(monkeypatch):
    """
    Test vector search when the index exists and returns results
    """
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session

    # Mock index check
    mock_index_check_result = MagicMock()
    mock_index_check_result.single.return_value = True  # Index exists
    mock_session.run.side_effect = [
        mock_index_check_result,
        [  # Vector search results
            {"text": "chunk1", "score": 0.9, "source_file": "file1.txt", "chunk_index": 0, "document_id": "doc1"},
            {"text": "chunk2", "score": 0.8, "source_file": "file2.txt", "chunk_index": 1, "document_id": "doc2"},
        ]
    ]

    with patch("src.retrieval.retriever.GraphDatabase.driver", return_value=mock_driver):
        retriever = VectorRetriever()
        results = retriever.search_similar_chunks([0.1] * 10, top_k=2)

    assert len(results) == 2
    assert results[0].text == "chunk1"
    assert results[0].score == 0.9
    assert results[1].metadata["source_file"] == "file2.txt"
