import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path
import io

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))


class MockStreamlit:
    """Mock Streamlit module for testing"""
    
    def __init__(self):
        self.session_state = {}
        self._file_uploader_value = None
        self._button_clicked = False
        self._error_called = False
        self._success_called = False
        self._spinner_called = False
        self._error_message = ""
        self._success_message = ""
    
    def title(self, text):
        pass
    
    def file_uploader(self, label, type=None, help=None):
        if type == ['txt']:
            return self._file_uploader_value
        return None
    
    def button(self, label, disabled=False):
        if disabled:
            return False
        return self._button_clicked
    
    def error(self, message):
        self._error_called = True
        self._error_message = message
    
    def success(self, message):
        self._success_called = True
        self._success_message = message
    
    def spinner(self, text):
        self._spinner_called = True
        return SpinnerContext()
    
    def markdown(self, text):
        pass


class SpinnerContext:
    """Context manager for spinner mock"""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockUploadedFile:
    """Mock uploaded file object"""
    
    def __init__(self, content: bytes, name: str):
        self.content = content
        self.name = name
    
    def read(self):
        return self.content


class TestDocumentUploadPage:
    
    def setup_method(self):
        """Setup for each test method"""
        self.mock_st = MockStreamlit()
        self.mock_rag_client = Mock()
    
    def test_page_renders_without_file(self):
        """Test that page renders correctly without a file selected"""
        from src.ui.pages.document_upload import render_page
        
        # No file selected
        self.mock_st._file_uploader_value = None
        
        # Should not raise any exceptions
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
    
    def test_file_upload_success(self):
        """Test successful file upload"""
        from src.ui.pages.document_upload import render_page
        
        # Mock uploaded file
        file_content = b"This is test document content."
        uploaded_file = MockUploadedFile(file_content, "test_document.txt")
        self.mock_st._file_uploader_value = uploaded_file
        self.mock_st._button_clicked = True
        
        # Mock successful RAG client response
        self.mock_rag_client.upload_file.return_value = {
            "ok": True,
            "data": {"message": "Document ingested successfully"}
        }
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verify RAG client was called correctly
        self.mock_rag_client.upload_file.assert_called_once_with(file_content, "test_document.txt")
        
        # Verify success message was shown
        assert self.mock_st._success_called
        assert "Documento enviado com sucesso!" in self.mock_st._success_message
        assert self.mock_st._spinner_called
    
    def test_file_upload_error(self):
        """Test file upload with error response"""
        from src.ui.pages.document_upload import render_page
        
        # Mock uploaded file
        file_content = b"This is test document content."
        uploaded_file = MockUploadedFile(file_content, "test_document.txt")
        self.mock_st._file_uploader_value = uploaded_file
        self.mock_st._button_clicked = True
        
        # Mock error RAG client response
        self.mock_rag_client.upload_file.return_value = {
            "ok": False,
            "error": "Server error"
        }
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Verify error message was shown
        assert self.mock_st._error_called
        assert "Erro ao enviar documento" in self.mock_st._error_message
        assert "Server error" in self.mock_st._error_message
    
    def test_no_file_selected_button_click(self):
        """Test button click without file selected"""
        from src.ui.pages.document_upload import render_page
        
        # No file selected but button clicked
        self.mock_st._file_uploader_value = None
        self.mock_st._button_clicked = True
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Should not call RAG client
        self.mock_rag_client.upload_file.assert_not_called()
        
        # Should not show success or error messages
        assert not self.mock_st._success_called
        assert not self.mock_st._error_called
    
    def test_file_selected_no_button_click(self):
        """Test file selected but button not clicked"""
        from src.ui.pages.document_upload import render_page
        
        # File selected but button not clicked
        file_content = b"This is test document content."
        uploaded_file = MockUploadedFile(file_content, "test_document.txt")
        self.mock_st._file_uploader_value = uploaded_file
        self.mock_st._button_clicked = False
        
        render_page(rag_client=self.mock_rag_client, st=self.mock_st)
        
        # Should not call RAG client
        self.mock_rag_client.upload_file.assert_not_called()
    
    def test_default_rag_client_initialization(self):
        """Test that default RAG client is created when none provided"""
        from src.ui.pages.document_upload import render_page
        
        # Mock RAGClient import at the module level where it's imported
        with patch('src.api.client.RAGClient') as mock_rag_client_class:
            mock_instance = Mock()
            mock_rag_client_class.return_value = mock_instance
            
            render_page(rag_client=None, st=self.mock_st)
            
            # Verify RAGClient was instantiated
            mock_rag_client_class.assert_called_once()
    
    def test_default_streamlit_import(self):
        """Test that streamlit is imported when st=None"""
        from src.ui.pages.document_upload import render_page
        
        # Mock streamlit module import
        with patch('builtins.__import__') as mock_import:
            mock_streamlit = Mock()
            mock_streamlit.title = Mock()
            mock_streamlit.file_uploader = Mock(return_value=None)
            mock_streamlit.button = Mock(return_value=False)
            mock_streamlit.markdown = Mock()
            
            def import_side_effect(name, *args, **kwargs):
                if name == 'streamlit':
                    return mock_streamlit
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            render_page(rag_client=self.mock_rag_client, st=None)
            
            # Verify streamlit functions were called
            mock_streamlit.title.assert_called()
            mock_streamlit.file_uploader.assert_called()
            mock_streamlit.button.assert_called()