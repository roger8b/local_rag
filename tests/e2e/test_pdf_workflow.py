"""
Testes end-to-end para fluxo PDF completo
"""
import pytest
from unittest.mock import patch, AsyncMock
from src.application.services.ingestion_service import IngestionService
from src.application.services.document_loaders import DocumentLoaderFactory


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


@pytest.mark.e2e
class TestPDFWorkflow:
    """Testes end-to-end para fluxo PDF completo"""
    
    def test_pdf_loader_integration(self):
        """Testa integração do document loader factory com PDF"""
        pdf_content = create_sample_pdf_bytes("Test content for integration")
        
        # Usar factory para obter loader
        loader = DocumentLoaderFactory.get_loader("test.pdf", pdf_content)
        
        # Extrair texto
        extracted_text = loader.extract_text()
        
        # Verificar que texto foi extraído
        assert "Test content for integration" in extracted_text
        assert len(extracted_text) > 0
    
    @pytest.mark.asyncio
    async def test_pdf_ingestion_workflow(self):
        """Testa fluxo completo de ingestão de PDF"""
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
            
            # Criar serviço de ingestão
            service = IngestionService()
            service._db_disabled = True  # Desabilitar BD para teste
            
            # Criar PDF com conteúdo específico
            pdf_content = create_sample_pdf_bytes("O céu é azul devido ao espalhamento de Rayleigh")
            
            # Executar ingestão
            result = await service.ingest_from_file_upload(
                pdf_content,
                "physics.pdf"
            )
            
            # Verificar resultado
            assert result["status"] == "success"
            assert result["chunks_created"] > 0
            assert result["document_id"] is not None
            assert result["filename"] == "physics.pdf"
    
    def test_txt_workflow_not_broken(self):
        """Testa que workflow TXT não foi quebrado"""
        txt_content = b"This is a test text document for regression testing"
        
        # Usar factory para obter loader
        loader = DocumentLoaderFactory.get_loader("test.txt", txt_content)
        
        # Extrair texto
        extracted_text = loader.extract_text()
        
        # Verificar que texto foi extraído
        assert extracted_text == "This is a test text document for regression testing"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_file(self):
        """Testa tratamento de erro para tipos de arquivo inválidos"""
        service = IngestionService()
        
        # Tentar processar arquivo não suportado
        with pytest.raises(ValueError, match="Unsupported file type"):
            await service.ingest_from_file_upload(
                b"some content",
                "document.docx"
            )