"""
Testes de integração para ingestão de documentos PDF
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.application.services.ingestion_service import IngestionService


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


@pytest.mark.asyncio
class TestIngestionServicePDF:
    """Testes de integração para ingestão de PDFs"""
    
    async def test_ingest_pdf_document(self):
        """Testa ingestão completa de PDF"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            service = IngestionService()
            service._db_disabled = True  # Desabilitar BD para teste
            
            pdf_content = create_sample_pdf_bytes("Test PDF content")
            
            result = await service.ingest_from_file_upload(
                pdf_content, 
                "test.pdf"
            )
            
            assert result["status"] == "success"
            assert result["chunks_created"] > 0
            assert result["document_id"] is not None
            assert result["filename"] == "test.pdf"
    
    async def test_txt_ingestion_still_works(self):
        """Testa regressão - TXT deve continuar funcionando"""
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            service = IngestionService()
            service._db_disabled = True  # Desabilitar BD para teste
            
            txt_content = b"Sample text content for testing"
            
            result = await service.ingest_from_file_upload(
                txt_content,
                "test.txt"
            )
            
            assert result["status"] == "success"
            assert result["chunks_created"] > 0
    
    async def test_unsupported_file_type_rejected(self):
        """Testa rejeição de tipos de arquivo não suportados"""
        service = IngestionService()
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            await service.ingest_from_file_upload(
                b"some content",
                "document.docx"
            )