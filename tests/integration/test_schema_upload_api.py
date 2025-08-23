"""
Testes de integração para os endpoints de upload e cache de documentos para schema
Seguindo metodologia TDD para História 7: Upload de Documento para Inferência de Schema
"""
import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from src.main import app
from src.application.services.document_cache_service import get_document_cache_service, close_document_cache_service


class TestSchemaUploadEndpoints:
    """Testes para endpoints de upload e cache de documentos"""
    
    def setup_method(self):
        """Setup para cada teste - limpar cache"""
        # Clean cache before each test
        close_document_cache_service()  # Reset the singleton
    
    def teardown_method(self):
        """Cleanup após cada teste"""
        close_document_cache_service()
    
    def test_schema_upload_endpoint_exists(self):
        """
        AC 1: Test que endpoint POST /api/v1/schema/upload existe
        """
        client = TestClient(app)
        
        # Create a simple text file
        file_content = b"Test document content for schema analysis"
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        # Should not be 404
        assert response.status_code != 404
        assert response.status_code in [201, 415, 422]  # Created, unsupported type, or validation error
    
    def test_schema_upload_txt_file_success(self):
        """
        AC 1: Test upload de arquivo .txt retorna chave e metadados
        """
        client = TestClient(app)
        
        # Create a text file
        file_content = b"Joao Silva trabalha na empresa TechCorp desenvolvendo aplicacoes web com React e Node.js."
        files = {"file": ("document.txt", file_content, "text/plain")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verificar estrutura da resposta
        assert "key" in data
        assert "filename" in data
        assert "file_size_bytes" in data
        assert "text_stats" in data
        assert "processing_time_ms" in data
        assert "created_at" in data
        assert "expires_at" in data
        assert "file_type" in data
        
        # Verificar conteúdo
        assert data["filename"] == "document.txt"
        assert data["file_size_bytes"] == len(file_content)
        assert data["text_stats"]["total_chars"] > 0
        assert data["file_type"] == "txt"
        assert len(data["key"]) == 36  # UUID format
    
    def test_schema_upload_pdf_file_success(self):
        """
        Test upload de arquivo PDF (mockado)
        """
        with patch('src.application.services.document_loaders.DocumentLoaderFactory.get_loader') as mock_factory:
            # Mock PDF loader
            mock_loader = MagicMock()
            mock_loader.extract_text.return_value = "Extracted PDF content for schema analysis"
            mock_factory.return_value = mock_loader
            
            client = TestClient(app)
            
            # Create a fake PDF file
            file_content = b"%PDF-1.4 fake pdf content"
            files = {"file": ("document.pdf", file_content, "application/pdf")}
            
            response = client.post("/api/v1/schema/upload", files=files)
            
            assert response.status_code == 201
            data = response.json()
            
            assert data["filename"] == "document.pdf"
            assert data["file_type"] == "pdf"
            assert data["text_stats"]["total_chars"] > 0
    
    def test_schema_upload_invalid_file_type(self):
        """
        AC 6: Test que arquivo inválido retorna erro 415
        """
        client = TestClient(app)
        
        # Create an unsupported file type
        file_content = b"Invalid file content"
        files = {"file": ("document.docx", file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data
        assert "Unsupported file type" in data["detail"]
    
    def test_schema_upload_empty_file(self):
        """
        Test que arquivo vazio retorna erro 422
        """
        client = TestClient(app)
        
        # Create empty file
        files = {"file": ("empty.txt", b"", "text/plain")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()
    
    def test_schema_upload_file_too_large(self):
        """
        Test que arquivo muito grande retorna erro 413
        """
        client = TestClient(app)
        
        # Create file larger than 50MB (simulate)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("large.txt", large_content, "text/plain")}
        
        response = client.post("/api/v1/schema/upload", files=files)
        
        assert response.status_code == 413
        data = response.json()
        assert "detail" in data
        assert "too large" in data["detail"].lower()
    
    def test_schema_infer_with_document_key(self):
        """
        AC 2: Test inferência via chave de documento
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Person", "Company", "Technology"],
                "relationship_types": ["WORKS_AT", "USES", "DEVELOPS"]
            }
            
            client = TestClient(app)
            
            # First upload a document
            file_content = b"Joao Silva trabalha na TechCorp desenvolvendo com React."
            files = {"file": ("test.txt", file_content, "text/plain")}
            upload_response = client.post("/api/v1/schema/upload", files=files)
            
            assert upload_response.status_code == 201
            upload_data = upload_response.json()
            document_key = upload_data["key"]
            
            # Now infer schema using the key
            infer_response = client.post(
                "/api/v1/schema/infer",
                json={
                    "document_key": document_key,
                    "max_sample_length": 1000
                }
            )
            
            assert infer_response.status_code == 200
            infer_data = infer_response.json()
            
            # Verificar resposta
            assert infer_data["node_labels"] == ["Person", "Company", "Technology"]
            assert infer_data["relationship_types"] == ["WORKS_AT", "USES", "DEVELOPS"]
            assert infer_data["source"] == "llm"
            assert infer_data["document_info"] is not None
            assert infer_data["document_info"]["filename"] == "test.txt"
    
    def test_schema_infer_invalid_key(self):
        """
        Test que chave inválida retorna erro 404
        """
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "document_key": "invalid-key-12345",
                "max_sample_length": 500
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found or expired" in data["detail"]
    
    def test_schema_infer_validation_both_key_and_text(self):
        """
        Test que fornecer key E text gera erro 422
        """
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "document_key": "some-key",
                "text": "some text",
                "max_sample_length": 500
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "either" in data["detail"].lower() and "not both" in data["detail"].lower()
    
    def test_schema_infer_validation_neither_key_nor_text(self):
        """
        Test que não fornecer nem key nem text gera erro 422
        """
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/schema/infer",
            json={"max_sample_length": 500}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "must be provided" in data["detail"]
    
    def test_schema_infer_backward_compatibility(self):
        """
        Test que endpoint infer ainda funciona com texto direto (backward compatibility)
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Entity", "Concept"],
                "relationship_types": ["RELATED_TO", "MENTIONS"]
            }
            
            client = TestClient(app)
            
            response = client.post(
                "/api/v1/schema/infer",
                json={
                    "text": "Test text for backward compatibility",
                    "max_sample_length": 500
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "node_labels" in data
            assert "relationship_types" in data
            assert data["document_info"] is None  # No document info for direct text
    
    def test_list_schema_documents_empty(self):
        """
        AC 5: Test listagem de documentos quando cache vazio
        """
        client = TestClient(app)
        
        response = client.get("/api/v1/schema/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert "total_documents" in data
        assert "memory_usage_mb" in data
        assert "max_documents" in data
        assert "ttl_minutes" in data
        
        assert data["total_documents"] == 0
        assert data["documents"] == []
    
    def test_list_schema_documents_with_content(self):
        """
        AC 5: Test listagem de documentos com conteúdo
        """
        client = TestClient(app)
        
        # Upload some documents first
        files1 = {"file": ("doc1.txt", b"Content 1", "text/plain")}
        files2 = {"file": ("doc2.txt", b"Content 2", "text/plain")}
        
        upload1 = client.post("/api/v1/schema/upload", files=files1)
        upload2 = client.post("/api/v1/schema/upload", files=files2)
        
        assert upload1.status_code == 201
        assert upload2.status_code == 201
        
        # List documents
        response = client.get("/api/v1/schema/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_documents"] == 2
        assert len(data["documents"]) == 2
        
        # Verify document info
        doc_filenames = [doc["filename"] for doc in data["documents"]]
        assert "doc1.txt" in doc_filenames
        assert "doc2.txt" in doc_filenames
    
    def test_remove_schema_document_success(self):
        """
        AC 4: Test remoção manual de documento
        """
        client = TestClient(app)
        
        # Upload a document first
        files = {"file": ("test.txt", b"Test content", "text/plain")}
        upload_response = client.post("/api/v1/schema/upload", files=files)
        
        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        document_key = upload_data["key"]
        
        # Remove the document
        remove_response = client.delete(f"/api/v1/schema/documents/{document_key}")
        
        assert remove_response.status_code == 200
        remove_data = remove_response.json()
        
        assert remove_data["message"] == "Document removed successfully"
        assert remove_data["key"] == document_key
        
        # Verify it's removed by trying to use it
        infer_response = client.post(
            "/api/v1/schema/infer",
            json={"document_key": document_key}
        )
        
        assert infer_response.status_code == 404
    
    def test_remove_schema_document_not_found(self):
        """
        Test remoção de documento inexistente retorna 404
        """
        client = TestClient(app)
        
        response = client.delete("/api/v1/schema/documents/nonexistent-key")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    def test_schema_upload_no_text_extracted(self):
        """
        Test que arquivo sem texto extraível retorna erro 422
        """
        with patch('src.application.services.document_loaders.DocumentLoaderFactory.get_loader') as mock_factory:
            # Mock loader that returns empty text
            mock_loader = MagicMock()
            mock_loader.extract_text.return_value = ""
            mock_factory.return_value = mock_loader
            
            client = TestClient(app)
            
            files = {"file": ("empty.txt", b"fake content", "text/plain")}
            response = client.post("/api/v1/schema/upload", files=files)
            
            assert response.status_code == 422
            data = response.json()
            assert "No text content could be extracted" in data["detail"]