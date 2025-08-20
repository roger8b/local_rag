from unittest.mock import patch, Mock

from src.api.client import RAGClient


def test_query_includes_provider_in_payload():
    client = RAGClient(base_url="http://localhost:8000")
    with patch("src.api.client.requests.post") as mock_post:
        mock_resp = Mock()
        mock_resp.json.return_value = {"answer": "ok"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        client.query("what?", provider="gemini")
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["provider"] == "gemini"
