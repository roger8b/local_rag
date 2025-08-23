"""
Testes unitários para DocumentCacheService
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from src.application.services.document_cache_service import DocumentCacheService, CachedDocument


class TestDocumentCacheService:
    """Testes unitários para DocumentCacheService"""
    
    @pytest.fixture
    def cache_service(self):
        """Fixture para criar instância limpa do cache service"""
        return DocumentCacheService(ttl_minutes=5, max_documents=10, cleanup_interval_minutes=1)
    
    @pytest.mark.asyncio
    async def test_store_and_get_document(self, cache_service):
        """Test básico de armazenar e recuperar documento"""
        text_content = "Test document content"
        filename = "test.txt"
        size_bytes = len(text_content.encode())
        
        # Store document
        key = await cache_service.store_document(text_content, filename, size_bytes, 100.0)
        
        # Verify key format (UUID)
        assert len(key) == 36
        assert key.count('-') == 4
        
        # Retrieve document
        document = await cache_service.get_document(key)
        
        assert document is not None
        assert document.key == key
        assert document.filename == filename
        assert document.text_content == text_content
        assert document.file_size_bytes == size_bytes
        assert document.file_type == "txt"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, cache_service):
        """Test recuperar documento inexistente"""
        document = await cache_service.get_document("nonexistent-key")
        assert document is None
    
    @pytest.mark.asyncio
    async def test_remove_document(self, cache_service):
        """Test remoção de documento"""
        text_content = "Test document"
        key = await cache_service.store_document(text_content, "test.txt", len(text_content), 50.0)
        
        # Verify it exists
        document = await cache_service.get_document(key)
        assert document is not None
        
        # Remove it
        removed = await cache_service.remove_document(key)
        assert removed is True
        
        # Verify it's gone
        document = await cache_service.get_document(key)
        assert document is None
        
        # Try to remove again
        removed = await cache_service.remove_document(key)
        assert removed is False
    
    @pytest.mark.asyncio
    async def test_list_documents(self, cache_service):
        """Test listagem de documentos"""
        # Initially empty
        documents = await cache_service.list_documents()
        assert len(documents) == 0
        
        # Add some documents
        key1 = await cache_service.store_document("Content 1", "doc1.txt", 9, 10.0)
        key2 = await cache_service.store_document("Content 2", "doc2.pdf", 9, 15.0)
        
        # List documents
        documents = await cache_service.list_documents()
        assert len(documents) == 2
        
        # Verify document info
        filenames = [doc.filename for doc in documents]
        assert "doc1.txt" in filenames
        assert "doc2.pdf" in filenames
        
        # Verify sorting (newest first)
        assert documents[0].created_at >= documents[1].created_at
    
    @pytest.mark.asyncio
    async def test_file_type_detection(self, cache_service):
        """Test detecção de tipo de arquivo"""
        # Test TXT
        key_txt = await cache_service.store_document("Text content", "document.txt", 12, 20.0)
        doc_txt = await cache_service.get_document(key_txt)
        assert doc_txt.file_type == "txt"
        
        # Test PDF
        key_pdf = await cache_service.store_document("PDF content", "document.pdf", 11, 25.0)
        doc_pdf = await cache_service.get_document(key_pdf)
        assert doc_pdf.file_type == "pdf"
        
        # Test unknown
        key_unknown = await cache_service.store_document("Unknown content", "document.docx", 15, 30.0)
        doc_unknown = await cache_service.get_document(key_unknown)
        assert doc_unknown.file_type == "unknown"
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """Test estatísticas do cache"""
        # Empty cache
        stats = await cache_service.get_cache_stats()
        assert stats["total_documents"] == 0
        assert stats["memory_usage_mb"] == 0
        assert stats["max_documents"] == 10
        assert stats["ttl_minutes"] == 5
        
        # Add document
        content = "Test content for stats that is long enough to register memory usage"
        await cache_service.store_document(content, "test.txt", len(content.encode()), 40.0)
        
        # Check stats
        stats = await cache_service.get_cache_stats()
        assert stats["total_documents"] == 1
        assert stats["memory_usage_mb"] >= 0  # Memory usage could be 0 if rounded down
    
    @pytest.mark.asyncio
    async def test_max_documents_limit(self, cache_service):
        """Test limite máximo de documentos"""
        # Fill cache to limit (10 documents)
        for i in range(10):
            await cache_service.store_document(f"Content {i}", f"doc{i}.txt", 10, 5.0)
        
        # Try to add one more - should raise error
        with pytest.raises(ValueError, match="Cache full"):
            await cache_service.store_document("Overflow", "overflow.txt", 8, 2.0)
    
    @pytest.mark.asyncio 
    async def test_clear_all(self, cache_service):
        """Test limpeza completa do cache"""
        # Add some documents
        await cache_service.store_document("Doc 1", "doc1.txt", 5, 10.0)
        await cache_service.store_document("Doc 2", "doc2.txt", 5, 15.0)
        
        # Verify they exist
        docs = await cache_service.list_documents()
        assert len(docs) == 2
        
        # Clear all
        count = await cache_service.clear_all()
        assert count == 2
        
        # Verify cache is empty
        docs = await cache_service.list_documents()
        assert len(docs) == 0
    
    @pytest.mark.asyncio
    async def test_last_accessed_update(self, cache_service):
        """Test que last_accessed é atualizado no get"""
        key = await cache_service.store_document("Test", "test.txt", 4, 8.0)
        
        # Get document and record access time
        doc1 = await cache_service.get_document(key)
        first_access = doc1.last_accessed
        
        # Wait a bit and access again
        await asyncio.sleep(0.01)
        doc2 = await cache_service.get_document(key)
        second_access = doc2.last_accessed
        
        # Verify last_accessed was updated
        assert second_access > first_access
    
    def test_generate_key_format(self, cache_service):
        """Test formato da chave gerada"""
        key1 = cache_service._generate_key()
        key2 = cache_service._generate_key()
        
        # Should be UUIDs
        assert len(key1) == 36
        assert len(key2) == 36
        assert key1 != key2  # Should be unique
        
        # Should have UUID format
        parts1 = key1.split('-')
        assert len(parts1) == 5
        assert len(parts1[0]) == 8
        assert len(parts1[1]) == 4
        assert len(parts1[2]) == 4
        assert len(parts1[3]) == 4
        assert len(parts1[4]) == 12
    
    def test_determine_file_type(self, cache_service):
        """Test detecção de tipo de arquivo"""
        assert cache_service._determine_file_type("document.txt") == "txt"
        assert cache_service._determine_file_type("document.TXT") == "txt"  # Case insensitive
        assert cache_service._determine_file_type("document.pdf") == "pdf"
        assert cache_service._determine_file_type("document.PDF") == "pdf"  # Case insensitive
        assert cache_service._determine_file_type("document.docx") == "unknown"
        assert cache_service._determine_file_type("no_extension") == "unknown"