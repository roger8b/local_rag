import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path
import io

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.main import app


client = TestClient(app)


class TestIngestEndpoint:
    """Test cases for the /api/v1/ingest endpoint following TDD approach"""
    
    def test_ingest_endpoint_not_implemented_yet(self):
        """
        AC 1: Test that we can POST to /ingest endpoint
        This test will initially fail until we implement the endpoint
        """
        # Prepare a test file
        test_content = "Este e um documento de teste para ingestao via API.".encode('utf-8')
        files = {"file": ("test.txt", test_content, "text/plain")}
        data = {"embedding_provider": "ollama"}  # ← Parâmetro essencial!
        
        response = client.post("/api/v1/ingest", files=files, data=data)
        
        # Initially this will fail with 404, then we implement to make it pass
        assert response.status_code in [200, 201], f"Expected success status, got {response.status_code}"
    
    def test_ingest_invalid_file_type(self):
        """
        AC 2: Test that unsupported files are rejected with 415 status
        """
        # Prepare a file with unsupported extension
        test_content = b"This is content of an unsupported file"
        files = {"file": ("test.docx", test_content, "application/docx")}
        
        response = client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 415
        assert "Unsupported file type" in response.text
    
    def test_ingest_no_file_provided(self):
        """
        Test that endpoint handles missing file gracefully
        """
        response = client.post("/api/v1/ingest")
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.application.services.ingestion_service.IngestionService.ingest_from_content')
    async def test_ingest_txt_file_success(self, mock_ingest):
        """
        AC 1: Test successful ingestion of .txt file
        """
        # Mock the ingestion service
        mock_ingest.return_value = {"document_id": "test-doc-123", "chunks_created": 2}
        
        # Prepare a valid txt file
        test_content = "Este e um documento de teste.\n\nEle tem multiplos paragrafos para testar a divisao em chunks.".encode('utf-8')
        files = {"file": ("test_document.txt", test_content, "text/plain")}
        
        response = client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 201
        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "success"
        assert "filename" in response_data
        assert response_data["filename"] == "test_document.txt"
    
    @patch('src.application.services.ingestion_service.IngestionService.ingest_from_content')
    async def test_ingest_service_error_handling(self, mock_ingest):
        """
        Test that service errors are handled properly
        """
        # Mock service to raise an exception
        mock_ingest.side_effect = Exception("Neo4j connection failed")
        
        test_content = b"Test content that will fail to ingest"
        files = {"file": ("test.txt", test_content, "text/plain")}
        
        response = client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 500
        response_data = response.json()
        assert "detail" in response_data
    
    @patch('src.retrieval.retriever.VectorRetriever.retrieve')
    @patch('src.generation.generator.ResponseGenerator.generate_response')
    @patch('src.application.services.ingestion_service.IngestionService.ingest_from_content')
    async def test_end_to_end_ingest_and_query(self, mock_ingest, mock_generate, mock_retrieve):
        """
        AC 3: Test that ingested document can be queried successfully
        End-to-end test following the user story
        """
        # Mock ingestion success
        mock_ingest.return_value = {"document_id": "e2e-test-doc", "chunks_created": 1}
        
        # Mock retrieval and generation for query
        from src.models.api_models import DocumentSource
        mock_retrieve.return_value = [
            DocumentSource(text="Este e um documento de teste para E2E.", score=0.95)
        ]
        mock_generate.return_value = "Este documento e um exemplo de teste que foi ingerido via API."
        
        # 1. Ingest document
        test_content = "Este e um documento de teste para E2E.".encode('utf-8')
        files = {"file": ("e2e_test.txt", test_content, "text/plain")}
        
        ingest_response = client.post("/api/v1/ingest", files=files)
        assert ingest_response.status_code == 201
        
        # 2. Query about the ingested content
        query_response = client.post(
            "/api/v1/query",
            json={"question": "O que é este documento?"}
        )
        
        assert query_response.status_code == 200
        query_data = query_response.json()
        assert "answer" in query_data
        assert "teste" in query_data["answer"].lower()


class TestIngestionServiceUnit:
    """Unit tests for the IngestionService class"""
    
    @pytest.fixture
    def ingestion_service(self):
        """Fixture to provide IngestionService instance"""
        from src.application.services.ingestion_service import IngestionService
        return IngestionService()
    
    @patch('src.retrieval.retriever.VectorRetriever.__init__')
    @patch('src.retrieval.retriever.VectorRetriever.close')
    async def test_ingest_from_content_creates_chunks(self, mock_close, mock_init, ingestion_service):
        """
        Test that ingest_from_content properly processes text content
        """
        mock_init.return_value = None
        
        with patch.object(ingestion_service, '_create_chunks') as mock_chunks, \
             patch.object(ingestion_service, '_generate_embeddings') as mock_embeddings, \
             patch.object(ingestion_service, '_save_to_neo4j') as mock_save:
            
            mock_chunks.return_value = ["chunk1", "chunk2"]
            mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4]]
            mock_save.return_value = "doc-123"
            
            result = await ingestion_service.ingest_from_content(
                content="Test content for chunking",
                filename="test.txt"
            )
            
            assert "document_id" in result
            assert "chunks_created" in result
            assert result["chunks_created"] == 2
            
            mock_chunks.assert_called_once_with("Test content for chunking")
            # Allow provider kwarg (default 'ollama')
            args, kwargs = mock_embeddings.call_args
            assert list(args) == [["chunk1", "chunk2"]]
            assert kwargs.get("provider") in (None, "ollama")
            mock_save.assert_called_once()


class TestFileValidation:
    """Test file validation logic"""
    
    def test_is_txt_file_valid_extension(self):
        """Test that .txt files are recognized as valid"""
        from src.application.services.ingestion_service import is_valid_file_type
        
        assert is_valid_file_type("document.txt") is True
        assert is_valid_file_type("my_file.TXT") is True  # Case insensitive
        assert is_valid_file_type("/path/to/file.txt") is True
    
    def test_is_txt_file_invalid_extension(self):
        """Test that unsupported files are rejected"""
        from src.application.services.ingestion_service import is_valid_file_type
        
        # PDF agora é válido
        assert is_valid_file_type("document.pdf") is True
        # Outros tipos ainda são inválidos
        assert is_valid_file_type("image.jpg") is False
        assert is_valid_file_type("data.csv") is False
        assert is_valid_file_type("script.py") is False
        assert is_valid_file_type("no_extension") is False
