import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app


class TestDocumentsAPI:
    def test_get_documents_success(self):
        client = TestClient(app)

        # Mock Neo4j session.run to return document records
        class FakeResult:
            def __init__(self, rows):
                self._rows = rows

            def __iter__(self):
                for r in self._rows:
                    yield r

        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session

            rows = [
                {"doc_id": "b", "filename": "b.txt", "filetype": "txt", "ingested_at": "2024-08-20T10:00:00Z"},
                {"doc_id": "a", "filename": "a.pdf", "filetype": "pdf", "ingested_at": "2024-08-21T09:00:00Z"},
            ]
            session.run.return_value = FakeResult(rows)

            resp = client.get("/api/v1/documents")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert {"doc_id", "filename", "filetype", "ingested_at"}.issubset(data[0].keys())

    def test_delete_document_success(self):
        client = TestClient(app)

        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session
            # No exception on run implies success
            resp = client.delete("/api/v1/documents/doc-123")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "deleted"
            assert body["doc_id"] == "doc-123"

    def test_list_document_chunks(self):
        client = TestClient(app)
        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session

            class FakeResult:
                def __iter__(self):
                    yield {"chunk_index": 0, "text": "Hello", "source_file": "a.txt"}
                    yield {"chunk_index": 1, "text": "World", "source_file": "a.txt"}

            session.run.return_value = FakeResult()

            resp = client.get("/api/v1/documents/doc-1/chunks?limit=2")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert data[0]["chunk_index"] == 0
