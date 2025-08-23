"""
Testes de integração para as melhorias na API de Schema (História 8)
- Informações detalhadas do documento
- Controle por percentual
- Seleção de modelo LLM
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app
from src.application.services.document_cache_service import get_document_cache_service, close_document_cache_service


class TestSchemaImprovements:
    """Testes para as melhorias na API de Schema"""
    
    def setup_method(self):
        """Setup para cada teste - limpar cache"""
        close_document_cache_service()  # Reset the singleton
    
    def teardown_method(self):
        """Cleanup após cada teste"""
        close_document_cache_service()
    
    def test_upload_returns_detailed_stats(self):
        """
        Test que upload retorna estatísticas detalhadas do texto
        """
        client = TestClient(app)
        
        # Create test content with known statistics
        test_content = "Line 1\nLine 2\nLine 3\nThis is a test document with multiple words."
        file_content = test_content.encode('utf-8')
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify new fields exist
        assert "file_size_bytes" in data
        assert "text_stats" in data
        assert "processing_time_ms" in data
        
        # Verify text statistics
        text_stats = data["text_stats"]
        assert "total_chars" in text_stats
        assert "total_words" in text_stats
        assert "total_lines" in text_stats
        
        # Verify actual values
        assert text_stats["total_chars"] == len(test_content)
        assert text_stats["total_words"] == len(test_content.split())
        assert text_stats["total_lines"] == test_content.count('\n') + 1
        assert data["file_size_bytes"] == len(file_content)
        assert isinstance(data["processing_time_ms"], (int, float))
        assert data["processing_time_ms"] > 0
    
    def test_schema_infer_with_percentage(self):
        """
        Test inferência usando percentual
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Person", "Document"],
                "relationship_types": ["WRITES", "CONTAINS"]
            }
            
            client = TestClient(app)
            
            # First upload a document
            test_content = "A" * 1000  # 1000 characters
            files = {"file": ("test.txt", test_content.encode(), "text/plain")}
            upload_response = client.post("/api/v1/schema/upload", files=files)
            
            assert upload_response.status_code == 201
            document_key = upload_response.json()["key"]
            
            # Test with 50% percentage
            infer_response = client.post(
                "/api/v1/schema/infer",
                json={
                    "document_key": document_key,
                    "sample_percentage": 50
                }
            )
            
            assert infer_response.status_code == 200
            data = infer_response.json()
            
            # Verify that mock was called with 50% of content (500 chars)
            mock_infer.assert_called_once()
            called_text = mock_infer.call_args[0][0]
            assert len(called_text) == 500
            
            # Verify document_info includes percentage information
            assert "document_info" in data
            assert data["document_info"]["sample_percentage"] == 50.0
    
    def test_schema_infer_backward_compatibility_max_sample_length(self):
        """
        Test que max_sample_length ainda funciona (backward compatibility)
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Test"],
                "relationship_types": ["RELATES"]
            }
            
            client = TestClient(app)
            
            # Upload document
            test_content = "A" * 1000  # 1000 characters
            files = {"file": ("test.txt", test_content.encode(), "text/plain")}
            upload_response = client.post("/api/v1/schema/upload", files=files)
            document_key = upload_response.json()["key"]
            
            # Test with absolute character count (should override percentage)
            infer_response = client.post(
                "/api/v1/schema/infer",
                json={
                    "document_key": document_key,
                    "sample_percentage": 80,  # This should be ignored
                    "max_sample_length": 300  # This should take precedence
                }
            )
            
            assert infer_response.status_code == 200
            
            # Verify that mock was called with 300 chars (not 80%)
            called_text = mock_infer.call_args[0][0]
            assert len(called_text) == 300
    
    def test_schema_infer_with_provider_selection(self):
        """
        Test seleção de provider LLM
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Custom"],
                "relationship_types": ["CUSTOM_REL"]
            }
            
            client = TestClient(app)
            
            # Upload document
            files = {"file": ("test.txt", b"Test content", "text/plain")}
            upload_response = client.post("/api/v1/schema/upload", files=files)
            document_key = upload_response.json()["key"]
            
            # Test with custom provider and model
            infer_response = client.post(
                "/api/v1/schema/infer",
                json={
                    "document_key": document_key,
                    "sample_percentage": 100,
                    "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini"
                }
            )
            
            assert infer_response.status_code == 200
            data = infer_response.json()
            
            # Verify that provider and model were passed correctly
            mock_infer.assert_called_once()
            args, kwargs = mock_infer.call_args
            assert kwargs["provider_override"] == "openai"
            assert kwargs["model_override"] == "gpt-4o-mini"
            
            # Verify response includes provider info
            assert data["model_used"] == "openai:gpt-4o-mini"
    
    def test_schema_infer_direct_text_with_provider(self):
        """
        Test seleção de provider com texto direto (backward compatibility)
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Entity"],
                "relationship_types": ["RELATES"]
            }
            
            client = TestClient(app)
            
            response = client.post(
                "/api/v1/schema/infer",
                json={
                    "text": "Test text for direct analysis",
                    "sample_percentage": 100,
                    "llm_provider": "gemini",
                    "llm_model": "gemini-1.5-pro"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify provider was used
            mock_infer.assert_called_once()
            args, kwargs = mock_infer.call_args
            assert kwargs["provider_override"] == "gemini"
            assert kwargs["model_override"] == "gemini-1.5-pro"
            
            assert data["model_used"] == "gemini:gemini-1.5-pro"
            assert data["document_info"] is None  # No document info for direct text
    
    def test_list_documents_returns_detailed_info(self):
        """
        Test que listagem de documentos retorna informações detalhadas
        """
        client = TestClient(app)
        
        # Upload a document with known content
        test_content = "Test document\nWith two lines\nAnd multiple words here."
        files = {"file": ("detailed_test.txt", test_content.encode(), "text/plain")}
        upload_response = client.post("/api/v1/schema/upload", files=files)
        
        assert upload_response.status_code == 201
        
        # List documents
        list_response = client.get("/api/v1/schema/documents")
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        assert data["total_documents"] == 1
        assert len(data["documents"]) == 1
        
        doc = data["documents"][0]
        
        # Verify new detailed fields
        assert "file_size_bytes" in doc
        assert "text_stats" in doc
        
        text_stats = doc["text_stats"]
        assert text_stats["total_chars"] == len(test_content)
        assert text_stats["total_words"] == len(test_content.split())
        assert text_stats["total_lines"] == test_content.count('\n') + 1
    
    def test_percentage_validation(self):
        """
        Test validação de percentual (0-100)
        """
        client = TestClient(app)
        
        # Upload document
        files = {"file": ("test.txt", b"Test", "text/plain")}
        upload_response = client.post("/api/v1/schema/upload", files=files)
        document_key = upload_response.json()["key"]
        
        # Test invalid percentage (> 100)
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "document_key": document_key,
                "sample_percentage": 150  # Invalid
            }
        )
        
        assert response.status_code == 422
        
        # Test negative percentage
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "document_key": document_key,
                "sample_percentage": -10  # Invalid
            }
        )
        
        assert response.status_code == 422
    
    def test_minimum_sample_size_with_percentage(self):
        """
        Test que percentual pequeno resulta em tamanho mínimo de 50 caracteres
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Test"],
                "relationship_types": ["TEST"]
            }
            
            client = TestClient(app)
            
            # Upload very small document
            test_content = "Small text"  # Only 10 characters
            files = {"file": ("small.txt", test_content.encode(), "text/plain")}
            upload_response = client.post("/api/v1/schema/upload", files=files)
            document_key = upload_response.json()["key"]
            
            # Test with very small percentage that would result in < 50 chars
            infer_response = client.post(
                "/api/v1/schema/infer",
                json={
                    "document_key": document_key,
                    "sample_percentage": 10  # 10% of 10 chars = 1 char
                }
            )
            
            assert infer_response.status_code == 200
            
            # Should use the full text since it's less than minimum 50 chars
            called_text = mock_infer.call_args[0][0]
            assert len(called_text) == len(test_content)  # Should use full text