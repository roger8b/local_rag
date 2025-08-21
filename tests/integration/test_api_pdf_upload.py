"""
Testes de integração para API de upload de PDFs
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app


def create_sample_pdf_bytes(text_content: str = "sample text") -> bytes:
    """Helper para criar PDF de teste minimalista"""
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


class TestAPIPDFUpload:
    """Testes da API para upload de PDFs"""
    
    def test_api_upload_pdf(self):
        """Testa upload de PDF via API"""
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
            pdf_content = create_sample_pdf_bytes("Test PDF for API upload")
            files = {"file": ("test.pdf", pdf_content, "application/pdf")}
            
            response = client.post(
                "/api/v1/ingest",
                files=files
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == "test.pdf"
            assert "document_id" in data
            assert data["chunks_created"] > 0
    
    def test_api_upload_txt_still_works(self):
        """Testa que upload de TXT ainda funciona após mudanças"""
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
            txt_content = b"Test text file content"
            files = {"file": ("test.txt", txt_content, "text/plain")}
            
            response = client.post(
                "/api/v1/ingest",
                files=files
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["filename"] == "test.txt"
    
    def test_api_reject_unsupported_file(self):
        """Testa rejeição de arquivo não suportado"""
        client = TestClient(app)
        files = {"file": ("test.docx", b"content", "application/docx")}
        
        response = client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 415
        data = response.json()
        assert "Unsupported file type" in data["detail"]
    
    def test_api_empty_file_rejection(self):
        """Testa rejeição de arquivo vazio"""
        client = TestClient(app)
        files = {"file": ("test.pdf", b"", "application/pdf")}
        
        response = client.post("/api/v1/ingest", files=files)
        
        assert response.status_code == 422
        data = response.json()
        assert "empty" in data["detail"].lower()