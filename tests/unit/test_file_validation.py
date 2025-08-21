"""
Testes unitários para validação de tipos de arquivo
"""
import pytest
from src.application.services.ingestion_service import is_valid_file_type


class TestFileValidation:
    """Testes para validação de tipos de arquivo"""
    
    def test_is_valid_pdf_file(self):
        """Testa se arquivos PDF são reconhecidos como válidos"""
        assert is_valid_file_type("document.pdf") == True
        assert is_valid_file_type("document.PDF") == True
        assert is_valid_file_type("my-file.pdf") == True
    
    def test_is_valid_txt_file(self):
        """Testa se arquivos TXT continuam sendo válidos"""
        assert is_valid_file_type("document.txt") == True
        assert is_valid_file_type("document.TXT") == True
    
    def test_invalid_file_types(self):
        """Testa rejeição de tipos não suportados"""
        assert is_valid_file_type("image.jpg") == False
        assert is_valid_file_type("document.docx") == False
        assert is_valid_file_type("file.xlsx") == False
        assert is_valid_file_type("script.py") == False