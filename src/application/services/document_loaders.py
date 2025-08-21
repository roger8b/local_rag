"""
Document Loaders for different file types
"""
from abc import ABC, abstractmethod
from pypdf import PdfReader
import io


class DocumentLoader(ABC):
    """Abstract base class for document loaders"""
    
    @abstractmethod
    def extract_text(self) -> str:
        """Extract text from the document"""
        pass


class PDFDocumentLoader(DocumentLoader):
    """Loader for PDF documents using pypdf"""
    
    def __init__(self, content: bytes):
        self.content = content
    
    def extract_text(self) -> str:
        """Extract text from PDF content"""
        pdf_file = io.BytesIO(self.content)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()


class TextDocumentLoader(DocumentLoader):
    """Loader for text documents"""
    
    def __init__(self, content: bytes):
        self.content = content
    
    def extract_text(self) -> str:
        """Extract text from text content"""
        return self.content.decode('utf-8')


class DocumentLoaderFactory:
    """Factory class for creating document loaders"""
    
    @staticmethod
    def get_loader(filename: str, content: bytes) -> DocumentLoader:
        """Get the appropriate document loader based on file extension"""
        if filename.lower().endswith('.pdf'):
            return PDFDocumentLoader(content)
        elif filename.lower().endswith('.txt'):
            return TextDocumentLoader(content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")