"""
Testes de integração para seleção de embedding provider na API de ingestão
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app


class TestAPIEmbeddingProvider:
    """Testes da API para seleção de embedding provider"""
    
    def test_api_ingest_with_ollama_provider(self):
        """Testa ingestão com provider ollama explicitamente especificado"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP para embeddings
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            client = TestClient(app)
            txt_content = b"Test text content"
            files = {"file": ("test.txt", txt_content, "text/plain")}
            data = {"embedding_provider": "ollama"}
            
            response = client.post(
                "/api/v1/ingest",
                files=files,
                data=data
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["status"] == "success"
            assert result["filename"] == "test.txt"
    
    def test_api_ingest_with_openai_provider(self):
        """Testa ingestão com provider openai"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP para embeddings
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"embedding": [0.1] * 1536}]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            client = TestClient(app)
            txt_content = b"Test text content"
            files = {"file": ("test.txt", txt_content, "text/plain")}
            data = {"embedding_provider": "openai"}
            
            response = client.post(
                "/api/v1/ingest",
                files=files,
                data=data
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["status"] == "success"
    
    def test_api_ingest_default_provider(self):
        """Testa ingestão sem especificar provider (usa padrão)"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP para embeddings
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            client = TestClient(app)
            txt_content = b"Test text content"
            files = {"file": ("test.txt", txt_content, "text/plain")}
            # Não especifica embedding_provider, deve usar padrão (ollama)
            
            response = client.post(
                "/api/v1/ingest",
                files=files
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["status"] == "success"
    
    def test_api_ingest_invalid_provider(self):
        """Testa rejeição de provider inválido"""
        client = TestClient(app)
        txt_content = b"Test text content"
        files = {"file": ("test.txt", txt_content, "text/plain")}
        data = {"embedding_provider": "invalid_provider"}
        
        response = client.post(
            "/api/v1/ingest",
            files=files,
            data=data
        )
        
        assert response.status_code == 422
        result = response.json()
        assert "Invalid embedding provider" in result["detail"]
        assert "invalid_provider" in result["detail"]
        assert "ollama" in result["detail"]
        assert "openai" in result["detail"]
    
    def test_api_ingest_pdf_with_custom_provider(self):
        """Testa ingestão de PDF com provider personalizado"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP para embeddings
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"embedding": [0.1] * 1536}]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Criar PDF usando o mesmo helper dos outros testes
            def create_sample_pdf_bytes(text_content: str = "sample text") -> bytes:
                pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
({text_content}) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000251 00000 n 
0000000341 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
423
%%EOF"""
                return pdf_content.encode('utf-8')
            
            pdf_content = create_sample_pdf_bytes("Test PDF with OpenAI embeddings")
            
            client = TestClient(app)
            files = {"file": ("test.pdf", pdf_content, "application/pdf")}
            data = {"embedding_provider": "openai"}
            
            response = client.post(
                "/api/v1/ingest",
                files=files,
                data=data
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["status"] == "success"
            assert result["filename"] == "test.pdf"