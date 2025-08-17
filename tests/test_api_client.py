import os
from unittest.mock import patch, MagicMock


def test_rag_client_success():
    from src.api.client import RAGClient

    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Resposta gerada",
            "sources": [{"text": "Fonte", "score": 0.9}],
            "question": "Pergunta?",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = RAGClient(base_url="http://localhost:8000")
        result = client.query("Pergunta?")

        assert result["ok"] is True
        assert result["data"]["answer"] == "Resposta gerada"


def test_rag_client_connection_error():
    from src.api.client import RAGClient
    import requests

    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = RAGClient(base_url="http://localhost:8000")
        result = client.query("Pergunta?")

        assert result["ok"] is False
        assert "Connection failed" in result["error"]


def test_rag_client_uses_env_var(monkeypatch):
    from src.api.client import RAGClient

    monkeypatch.setenv("API_BASE_URL", "http://custom:9000")
    client = RAGClient()
    assert client.base_url == "http://custom:9000"

