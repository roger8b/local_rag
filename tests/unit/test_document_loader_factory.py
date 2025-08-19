"""
Testes unitários para o Document Loader Factory
"""
import pytest
from src.application.services.document_loaders import DocumentLoaderFactory, PDFDocumentLoader, TextDocumentLoader


class TestDocumentLoaderFactory:
    """Testes para factory de document loaders"""
    
    def test_get_loader_for_pdf(self):
        """Testa criação de loader para PDF"""
        loader = DocumentLoaderFactory.get_loader("document.pdf", b"content")
        assert isinstance(loader, PDFDocumentLoader)
    
    def test_get_loader_for_txt(self):
        """Testa criação de loader para TXT"""
        loader = DocumentLoaderFactory.get_loader("document.txt", b"content")
        assert isinstance(loader, TextDocumentLoader)
    
    def test_get_loader_unsupported_type(self):
        """Testa exceção para tipo não suportado"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentLoaderFactory.get_loader("document.docx", b"content")
    
    def test_get_loader_case_insensitive(self):
        """Testa que detecção de tipo é case insensitive"""
        pdf_loader = DocumentLoaderFactory.get_loader("DOCUMENT.PDF", b"content")
        assert isinstance(pdf_loader, PDFDocumentLoader)
        
        txt_loader = DocumentLoaderFactory.get_loader("DOCUMENT.TXT", b"content")
        assert isinstance(txt_loader, TextDocumentLoader)