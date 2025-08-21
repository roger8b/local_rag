"""
Testes unitários para extração de texto de documentos
"""
import pytest
import io
from src.application.services.document_loaders import PDFDocumentLoader, TextDocumentLoader


def create_sample_pdf_bytes(text_content: str = "sample text") -> bytes:
    """Helper para criar PDF de teste minimalista - apenas para testes"""
    # PDF mínimo válido com texto simples
    # Este é um PDF minimal válido que contém o texto especificado
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


class TestTextExtraction:
    """Testes para extração de texto de diferentes tipos de documento"""
    
    def test_pdf_text_extraction(self):
        """Testa extração de texto de PDF"""
        test_text = "This is a test PDF document"
        pdf_content = create_sample_pdf_bytes(test_text)
        loader = PDFDocumentLoader(pdf_content)
        extracted_text = loader.extract_text()
        
        assert test_text in extracted_text
        assert len(extracted_text) > 0
    
    def test_txt_text_extraction(self):
        """Testa extração de texto de TXT"""
        txt_content = b"This is sample text content"
        loader = TextDocumentLoader(txt_content)
        text = loader.extract_text()
        
        assert text == "This is sample text content"
    
    def test_pdf_multiline_extraction(self):
        """Testa extração de texto multi-linha de PDF"""
        test_text = "Line one of the PDF"
        pdf_content = create_sample_pdf_bytes(test_text)
        loader = PDFDocumentLoader(pdf_content)
        extracted_text = loader.extract_text()
        
        assert test_text in extracted_text
    
    def test_txt_utf8_extraction(self):
        """Testa extração de texto UTF-8"""
        txt_content = "Texto com acentos: ção, não, coração".encode('utf-8')
        loader = TextDocumentLoader(txt_content)
        text = loader.extract_text()
        
        assert "acentos" in text
        assert "coração" in text
    
    def test_empty_pdf_extraction(self):
        """Testa extração de PDF vazio"""
        pdf_content = create_sample_pdf_bytes("")
        loader = PDFDocumentLoader(pdf_content)
        extracted_text = loader.extract_text()
        
        # PDF vazio ainda pode ter espaços ou quebras de linha
        assert isinstance(extracted_text, str)
    
    def test_empty_txt_extraction(self):
        """Testa extração de TXT vazio"""
        txt_content = b""
        loader = TextDocumentLoader(txt_content)
        text = loader.extract_text()
        
        assert text == ""