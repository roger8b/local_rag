import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.models.api_models import DocumentSource


client = TestClient(app)


def test_ingest_empty_file_returns_422():
    files = {"file": ("empty.txt", b"", "text/plain")}
    resp = client.post("/api/v1/ingest", files=files)
    assert resp.status_code == 422
    assert "File is empty" in resp.text


def test_query_with_provider_override_openai():
    with patch("src.retrieval.retriever.VectorRetriever.retrieve") as mock_retrieve, \
         patch("src.generation.generator.ResponseGenerator.generate_response") as mock_generate, \
         patch("src.retrieval.retriever.VectorRetriever.close") as mock_close:

        mock_retrieve.return_value = [DocumentSource(text="t", score=1.0)]
        mock_generate.return_value = "ans"

        resp = client.post("/api/v1/query", json={"question": "q", "provider": "openai"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider_used"] == "openai"


def test_query_generator_error_returns_500():
    with patch("src.retrieval.retriever.VectorRetriever.retrieve") as mock_retrieve, \
         patch("src.generation.generator.ResponseGenerator.generate_response") as mock_generate, \
         patch("src.retrieval.retriever.VectorRetriever.close") as mock_close:

        mock_retrieve.return_value = [DocumentSource(text="t", score=1.0)]
        mock_generate.side_effect = Exception("boom")

        resp = client.post("/api/v1/query", json={"question": "q"})
        assert resp.status_code == 500
        assert "Internal server error" in resp.text


def test_query_invalid_provider_returns_422():
    resp = client.post("/api/v1/query", json={"question": "q", "provider": "invalid"})
    assert resp.status_code == 422
