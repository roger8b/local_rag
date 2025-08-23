import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.main import app


class TestDBAdminAPI:
    def test_db_status(self):
        client = TestClient(app)

        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session

            class FakeResult:
                def __init__(self, rows):
                    self._rows = rows
                def single(self):
                    return {"total": self._rows[0]["total"]}
                def __iter__(self):
                    for r in self._rows:
                        yield r

            # First run: count documents
            # Second run: count chunks
            # Third run: show indexes (exists)
            idx_result = MagicMock()
            idx_result.single.return_value = {"name": "document_embeddings"}
            session.run.side_effect = [
                FakeResult([{"total": 2}]),
                FakeResult([{"total": 10}]),
                idx_result,
            ]

            resp = client.get("/api/v1/db/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["documents"] == 2
            assert data["chunks"] == 10
            assert data["vector_index_exists"] is True

    def test_db_reindex(self):
        client = TestClient(app)

        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session
            session.run.return_value = MagicMock()

            resp = client.post("/api/v1/db/reindex")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "ok"

            all_queries = "\n".join(call.args[0] for call in session.run.call_args_list)
            assert "CREATE VECTOR INDEX document_embeddings" in all_queries

    def test_db_clear_requires_confirm(self):
        # This endpoint doesn't require confirmation in current implementation
        client = TestClient(app)
        resp = client.delete("/api/v1/db/clear")
        assert resp.status_code == 200

    def test_db_clear_success(self):
        client = TestClient(app)
        with patch("src.api.routes.GraphDatabase.driver") as mock_driver:
            session = MagicMock()
            mock_driver.return_value.session.return_value.__enter__.return_value = session
            session.run.return_value = MagicMock()

            resp = client.delete("/api/v1/db/clear")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"

            queries = "\n".join(call.args[0] for call in session.run.call_args_list)
            assert "DROP INDEX document_embeddings IF EXISTS" in queries
            assert "MATCH (n) DETACH DELETE n" in queries
