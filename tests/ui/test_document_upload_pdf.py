"""
Testes da interface Streamlit para upload de PDFs
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from src.ui.pages.document_upload import render_page


class MockUploadedFile:
    """Mock para arquivos uploadados no Streamlit"""
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.position = 0
    
    def read(self):
        """Read file content"""
        return self.content
    
    def seek(self, position):
        """Seek to position"""
        self.position = position


def create_mock_streamlit():
    """Criar mock do Streamlit"""
    mock_st = Mock()
    mock_st.title = Mock()
    mock_st.subheader = Mock()
    mock_st.markdown = Mock()
    mock_st.file_uploader = Mock()
    mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
    mock_st.metric = Mock()
    mock_st.button = Mock()
    mock_st.success = Mock()
    mock_st.error = Mock()
    mock_st.warning = Mock()
    mock_st.spinner = Mock()
    mock_st.caption = Mock()
    return mock_st


def create_mock_rag_client():
    """Criar mock do RAGClient"""
    mock_client = Mock()
    mock_client.upload_file = Mock(return_value={"ok": True, "data": {"document_id": "test-123"}})
    return mock_client


class TestDocumentUploadPDF:
    """Testes simples para verificar se interface aceita PDFs"""
    
    def test_interface_accepts_pdf_extension(self):
        """Testa que o código da interface permite PDFs"""
        # Ler o arquivo da interface para verificar se permite PDF
        from pathlib import Path
        repo_root = Path(__file__).parents[2]
        interface_path = repo_root / "src/ui/pages/document_upload.py"
        with open(interface_path, "r") as f:
            content = f.read()
        
        # Verificar se 'pdf' está nos tipos aceitos
        assert "type=['txt', 'pdf']" in content
        
        # Verificar se a interface menciona PDF
        assert ".pdf" in content
