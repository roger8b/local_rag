import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
from pathlib import Path
import io

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.client import RAGClient


class TestRAGClient:
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = RAGClient(base_url="http://localhost:8000")
    
    def test_client_initialization(self):
        """Test RAGClient initialization with default and custom values"""
        # Default initialization
        default_client = RAGClient()
        assert default_client.base_url == "http://localhost:8000"
        assert default_client.timeout == 30.0
        
        # Custom initialization
        custom_client = RAGClient(base_url="http://example.com", timeout=60.0)
        assert custom_client.base_url == "http://example.com"
        assert custom_client.timeout == 60.0
    
    @patch('src.api.client.requests.post')
    def test_query_success(self, mock_post):
        """Test successful query method"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"answer": "Test answer", "sources": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.client.query("What is this about?")
        
        assert result["ok"] is True
        assert "data" in result
        assert result["data"]["answer"] == "Test answer"
        mock_post.assert_called_once_with(
            "http://localhost:8000/api/v1/query",
            json={"question": "What is this about?"},
            timeout=30.0
        )
    
    @patch('src.api.client.requests.post')
    def test_query_error(self, mock_post):
        """Test query method with request error"""
        # Mock request exception using requests.exceptions.RequestException
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = self.client.query("What is this about?")
        
        assert result["ok"] is False
        assert "error" in result
        assert "Connection error" in result["error"]


class TestRAGClientUploadFile:
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = RAGClient(base_url="http://localhost:8000")
    
    @patch('src.api.client.requests.post')
    def test_upload_file_success(self, mock_post):
        """Test successful file upload"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"message": "Document ingested successfully", "status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create test file content
        file_content = b"This is test document content."
        filename = "test_document.txt"
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is True
        assert "data" in result
        assert result["data"]["message"] == "Document ingested successfully"
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        # Check URL (first positional argument)
        assert call_args[0][0] == "http://localhost:8000/api/v1/ingest"
        assert call_args[1]["timeout"] == 30.0
        
        # Check that files parameter was passed
        assert "files" in call_args[1]
        files_arg = call_args[1]["files"]
        assert "file" in files_arg
        
        # Verify file tuple structure (filename, file_object, content_type)
        file_tuple = files_arg["file"]
        assert file_tuple[0] == filename
        assert hasattr(file_tuple[1], 'read')  # Should be file-like object
        assert file_tuple[2] == "text/plain"
    
    @patch('src.api.client.requests.post')
    def test_upload_file_http_error(self, mock_post):
        """Test file upload with HTTP error response"""
        # Mock HTTP error using requests.exceptions.HTTPError
        import requests
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP 500 Error")
        mock_post.return_value = mock_response
        
        file_content = b"This is test document content."
        filename = "test_document.txt"
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is False
        assert "error" in result
        assert "HTTP 500 Error" in result["error"]
    
    @patch('src.api.client.requests.post')
    def test_upload_file_request_exception(self, mock_post):
        """Test file upload with request exception"""
        # Mock request exception using requests.exceptions.RequestException
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Connection timeout")
        
        file_content = b"This is test document content."
        filename = "test_document.txt"
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is False
        assert "error" in result
        assert "Connection timeout" in result["error"]
    
    def test_upload_file_empty_content(self):
        """Test file upload with empty content"""
        file_content = b""
        filename = "empty_file.txt"
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is False
        assert "error" in result
        assert "File content cannot be empty" in result["error"]
    
    def test_upload_file_empty_filename(self):
        """Test file upload with empty filename"""
        file_content = b"This is test content."
        filename = ""
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is False
        assert "error" in result
        assert "Filename cannot be empty" in result["error"]
    
    def test_upload_file_non_txt_extension(self):
        """Test file upload with non-.txt extension"""
        file_content = b"This is test content."
        filename = "document.pdf"
        
        result = self.client.upload_file(file_content, filename)
        
        assert result["ok"] is False
        assert "error" in result
        assert "Only .txt files are supported" in result["error"]