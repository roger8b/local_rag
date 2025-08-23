import pytest
from unittest.mock import patch, mock_open, MagicMock
import sys
from pathlib import Path
import tempfile
import os
import requests

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the CLI script functions
from scripts.run_ingest import validate_file_exists, validate_file_type, upload_file, main


class TestFileValidation:
    """Test file validation functions"""
    
    def test_validate_file_exists_valid_file(self):
        """Test validation with existing file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            assert validate_file_exists(temp_path) is True
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_exists_nonexistent_file(self):
        """Test validation with non-existent file"""
        assert validate_file_exists("/nonexistent/path/file.txt") is False
    
    def test_validate_file_exists_directory(self):
        """Test validation with directory instead of file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            assert validate_file_exists(temp_dir) is False
    
    def test_validate_file_type_txt_files(self):
        """Test that .txt files are accepted"""
        assert validate_file_type("document.txt") is True
        assert validate_file_type("file.TXT") is True  # Case insensitive
        assert validate_file_type("/path/to/file.txt") is True
    
    def test_validate_file_type_non_txt_files(self):
        """Test that non-.txt files are rejected"""
        assert validate_file_type("document.pdf") is False
        assert validate_file_type("image.jpg") is False
        assert validate_file_type("data.csv") is False
        assert validate_file_type("no_extension") is False


class TestUploadFile:
    """Test file upload functionality"""
    
    @patch('requests.post')
    def test_upload_file_success(self, mock_post):
        """Test successful file upload"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "filename": "test.txt",
            "document_id": "doc-123",
            "chunks_created": 2
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for upload")
            temp_path = f.name
        
        try:
            result = upload_file(temp_path, "http://localhost:8000")
            
            assert result["status"] == "success"
            assert result["filename"] == "test.txt"
            assert result["chunks_created"] == 2
            
            # Verify API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "http://localhost:8000/api/v1/ingest" in call_args[0]
            assert "files" in call_args[1]
            
        finally:
            os.unlink(temp_path)
    
    @patch('requests.post')
    def test_upload_file_connection_error(self, mock_post):
        """Test connection error handling"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            with pytest.raises(requests.exceptions.ConnectionError):
                upload_file(temp_path, "http://localhost:8000")
        finally:
            os.unlink(temp_path)
    
    @patch('requests.post')
    def test_upload_file_http_error(self, mock_post):
        """Test HTTP error handling"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("415 Unsupported Media Type")
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            with pytest.raises(requests.exceptions.HTTPError):
                upload_file(temp_path, "http://localhost:8000")
        finally:
            os.unlink(temp_path)


class TestMainFunction:
    """Test the main CLI function"""
    
    @patch('scripts.run_ingest.upload_file')
    @patch('sys.argv', ['run_ingest.py', '--file', 'test.txt'])
    def test_main_success(self, mock_upload):
        """Test successful CLI execution"""
        # Mock file validation
        with patch('scripts.run_ingest.validate_file_exists', return_value=True), \
             patch('scripts.run_ingest.validate_file_type', return_value=True), \
             patch('scripts.run_ingest.print_response') as mock_print:
            
            mock_upload.return_value = {
                "status": "success",
                "filename": "test.txt",
                "document_id": "doc-123"
            }
            
            # Should not raise any exception
            try:
                main()
            except SystemExit as e:
                # main() should not exit on success
                assert e.code == 0 or e.code is None
            
            mock_upload.assert_called_once()
            mock_print.assert_called_once()
    
    @patch('sys.argv', ['run_ingest.py', '--file', 'nonexistent.txt'])
    def test_main_file_not_found(self):
        """Test CLI behavior when file doesn't exist"""
        with patch('scripts.run_ingest.validate_file_exists', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_with(1)
    
    @patch('sys.argv', ['run_ingest.py', '--file', 'document.pdf'])
    def test_main_invalid_file_type(self):
        """Test CLI behavior with invalid file type"""
        with patch('scripts.run_ingest.validate_file_exists', return_value=True), \
             patch('scripts.run_ingest.validate_file_type', return_value=False), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_with(1)
    
    @patch('scripts.run_ingest.upload_file')
    @patch('sys.argv', ['run_ingest.py', '--file', 'test.txt'])
    def test_main_connection_error(self, mock_upload):
        """Test CLI behavior when API is not reachable"""
        with patch('scripts.run_ingest.validate_file_exists', return_value=True), \
             patch('scripts.run_ingest.validate_file_type', return_value=True), \
             patch('sys.exit') as mock_exit:
            
            mock_upload.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            main()
            mock_exit.assert_called_with(1)
    
    @patch('scripts.run_ingest.upload_file')
    @patch('sys.argv', ['run_ingest.py', '--file', 'test.txt', '--api-url', 'http://custom:9000'])
    def test_main_custom_api_url(self, mock_upload):
        """Test CLI with custom API URL"""
        with patch('scripts.run_ingest.validate_file_exists', return_value=True), \
             patch('scripts.run_ingest.validate_file_type', return_value=True), \
             patch('scripts.run_ingest.print_response'):
            
            mock_upload.return_value = {"status": "success", "filename": "test.txt"}
            
            try:
                main()
            except SystemExit:
                pass
            
            # Verify custom URL was used
            mock_upload.assert_called_with('test.txt', 'http://custom:9000')
    
    @patch('scripts.run_ingest.upload_file')
    @patch('sys.argv', ['run_ingest.py', '--file', 'test.txt', '--verbose'])
    def test_main_verbose_mode(self, mock_upload):
        """Test CLI verbose mode"""
        with patch('scripts.run_ingest.validate_file_exists', return_value=True), \
             patch('scripts.run_ingest.validate_file_type', return_value=True), \
             patch('scripts.run_ingest.print_response'), \
             patch('os.path.getsize', return_value=1024), \
             patch('builtins.print') as mock_print:
            
            mock_upload.return_value = {"status": "success", "filename": "test.txt"}
            
            try:
                main()
            except SystemExit:
                pass
            
            # Verify verbose output was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            verbose_calls = [call for call in print_calls if "🔧" in call or "📁" in call]
            assert len(verbose_calls) >= 2  # Should have at least 2 verbose messages


class TestIntegrationScenarios:
    """Integration test scenarios matching AC requirements"""
    
    @patch('requests.post')
    def test_ac1_successful_upload(self, mock_post):
        """
        AC 1: Given API is running, when I send valid .txt file,
        then file is uploaded and response is printed
        """
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "success",
            "filename": "my_doc.txt",
            "document_id": "doc-456",
            "chunks_created": 3
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test document content for AC1")
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['run_ingest.py', '--file', temp_path]), \
                 patch('builtins.print') as mock_print:
                
                try:
                    main()
                except SystemExit:
                    pass
                
                # Verify success output was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                success_calls = [call for call in print_calls if "✅" in call]
                assert len(success_calls) >= 1
                
        finally:
            os.unlink(temp_path)
    
    def test_ac2_file_not_found(self):
        """
        AC 2: Given file doesn't exist, when I run script,
        then it shows file not found error without API call
        """
        nonexistent_file = "/tmp/definitely_does_not_exist.txt"
        
        with patch('sys.argv', ['run_ingest.py', '--file', nonexistent_file]), \
             patch('builtins.print') as mock_print, \
             patch('sys.exit') as mock_exit:
            
            main()
            
            # Should exit with error code
            mock_exit.assert_called_with(1)
            
            # Should print file not found error
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            error_calls = [call for call in print_calls if "File not found" in call]
            assert len(error_calls) >= 1
    
    @patch('requests.post')
    def test_ac3_api_not_running(self, mock_post):
        """
        AC 3: Given API is not running, when I run script,
        then it shows connection error
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            with patch('sys.argv', ['run_ingest.py', '--file', temp_path]), \
                 patch('builtins.print') as mock_print, \
                 patch('sys.exit') as mock_exit:
                
                main()
                
                # Should exit with error code
                mock_exit.assert_called_with(1)
                
                # Should print connection error
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                error_calls = [call for call in print_calls if "CONNECTION ERROR" in call]
                assert len(error_calls) >= 1
                
        finally:
            os.unlink(temp_path)