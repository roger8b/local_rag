import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def ingestion_service():
    from src.application.services.ingestion_service import IngestionService
    # Do not connect to real DB in these tests
    with patch("src.application.services.ingestion_service.GraphDatabase.driver"):
        service = IngestionService()
        yield service
        service.close()


class TestOllamaBatchEmbeddings:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_ollama_calls_single_post_with_input_list(self, mock_post, ingestion_service):
        chunks = [f"chunk {i}" for i in range(5)]
        # Simulate batch response with one embedding per input
        mock_post.return_value.json.return_value = {
            "embeddings": [[0.1] * 768 for _ in chunks]
        }

        result = await ingestion_service._generate_embeddings(chunks, provider="ollama")

        # One single POST
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/api/embeddings" in url or "/api/embed" in url
        payload = mock_post.call_args[1]["json"]
        assert payload.get("model")
        assert isinstance(payload.get("input"), list)
        assert payload["input"] == chunks
        assert len(result) == len(chunks)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_ollama_batch_count_mismatch_raises(self, mock_post, ingestion_service):
        chunks = ["a", "b", "c"]
        # Return fewer embeddings than inputs
        mock_post.return_value.json.return_value = {
            "embeddings": [[0.1] * 768 for _ in range(2)]
        }

        with pytest.raises(Exception):
            await ingestion_service._generate_embeddings(chunks, provider="ollama")


class TestNeo4jBulkInsert:
    @pytest.mark.asyncio
    async def test_save_to_neo4j_uses_unwind_single_query(self, ingestion_service):
        # Patch out driver/session to capture calls
        from src.application.services.ingestion_service import IngestionService

        fake_session = MagicMock()
        # First call for SHOW INDEXES -> indicate index missing
        fake_show_result = MagicMock()
        fake_show_result.single.return_value = None
        fake_session.run.side_effect = [fake_show_result, MagicMock()]

        fake_driver = MagicMock()
        fake_driver.session.return_value.__enter__.return_value = fake_session

        with patch.object(ingestion_service, "driver", fake_driver), \
             patch.object(ingestion_service, "_db_disabled", False):
            chunks = ["x", "y", "z"]
            embeds = [[0.1] * 8, [0.2] * 8, [0.3] * 8]

            # Force index ensure to run
            ingestion_service._ensure_vector_index()
            # Save data
            doc_id = ingestion_service._save_to_neo4j(chunks, embeds, filename="file.txt")

        # The second call to session.run should be the UNWIND create
        assert fake_session.run.call_count >= 2
        create_call = fake_session.run.call_args_list[-1]
        cypher = create_call[0][0]
        params = create_call[1]
        assert "UNWIND $chunks_data AS chunk" in cypher
        assert "CREATE (c:Chunk" in cypher
        assert "chunk.chunk_id" in cypher and "chunk.text" in cypher and "chunk.embedding" in cypher
        assert "document_id" in params and "source_file" in params and "chunks_data" in params
        assert isinstance(params["chunks_data"], list)
        assert len(params["chunks_data"]) == len(chunks)
        assert doc_id is not None


class TestOpenAIDimensions:
    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_openai_payload_includes_dimensions(self, mock_post, ingestion_service):
        with patch("src.application.services.ingestion_service.settings.openai_api_key", "sk-test"):
            # Configure custom dimension
            with patch("src.application.services.ingestion_service.settings.openai_embedding_dimensions", 256):
                chunks = ["a", "b"]
                mock_post.return_value.json.return_value = {
                    "data": [
                        {"embedding": [0.0] * 256},
                        {"embedding": [0.1] * 256},
                    ]
                }
                await ingestion_service._generate_embeddings(chunks, provider="openai")

                payload = mock_post.call_args[1]["json"]
                assert payload.get("dimensions") == 256

    def test_vector_index_uses_config_dimension(self, ingestion_service):
        from src.application.services.ingestion_service import IngestionService

        fake_session = MagicMock()
        fake_show_result = MagicMock()
        fake_show_result.single.return_value = None
        fake_session.run.side_effect = [fake_show_result, MagicMock()]

        fake_driver = MagicMock()
        fake_driver.session.return_value.__enter__.return_value = fake_session

        with patch.object(ingestion_service, "driver", fake_driver), \
             patch.object(ingestion_service, "_db_disabled", False), \
             patch("src.application.services.ingestion_service.settings.openai_embedding_dimensions", 256):
            ingestion_service._ensure_vector_index()

        # The second call should be the CREATE INDEX query
        assert fake_session.run.call_count >= 2
        create_call = fake_session.run.call_args_list[-1]
        cypher = create_call[0][0]
        assert "`vector.dimensions`: 256" in cypher
