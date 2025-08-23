import pytest
from unittest.mock import patch, MagicMock

from src.application.services.ingestion_service import IngestionService


import pytest


@pytest.mark.asyncio
async def test_ingestion_saves_document_and_part_of_relations(monkeypatch):
    # Mock driver/session
    with patch("src.application.services.ingestion_service.GraphDatabase.driver") as mock_driver:
        session = MagicMock()
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.session.return_value.__enter__.return_value = session

        svc = IngestionService()
        # Deterministic chunks and embeddings
        monkeypatch.setattr(svc, "_create_chunks", lambda content: ["c1", "c2"]) 
        async def fake_embed(chunks, provider="ollama"):
            return [[0.0], [0.1]]
        monkeypatch.setattr(svc, "_generate_embeddings", fake_embed)
        from unittest.mock import AsyncMock
        monkeypatch.setattr(svc, "_check_ollama_health", AsyncMock(return_value=False))

        result = await svc.ingest_from_content("content", "file.txt", embedding_provider="ollama")

        assert result["status"] == "success"
        # Ensure we attempted to create a Document and PART_OF links
        all_calls = "\n".join(c.args[0] for c in session.run.call_args_list)
        assert "CREATE (d:Document" in all_calls or "MERGE (d:Document" in all_calls
        assert "PART_OF" in all_calls
