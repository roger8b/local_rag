"""
DocumentCacheService - Gerencia documentos temporários em memória para inferência de schema
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TextStats:
    """Estatísticas do texto extraído"""
    total_chars: int
    total_words: int
    total_lines: int


@dataclass
class CachedDocument:
    """Representa um documento armazenado em cache"""
    key: str
    filename: str
    text_content: str
    file_type: str
    file_size_bytes: int
    text_stats: TextStats
    processing_time_ms: float
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime


@dataclass
class DocumentInfo:
    """Informações de um documento para listagem"""
    key: str
    filename: str
    file_size_bytes: int
    text_stats: TextStats
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime


class DocumentCacheService:
    """Serviço para cache temporário de documentos em memória"""
    
    def __init__(self, ttl_minutes: int = 30, max_documents: int = 100, cleanup_interval_minutes: int = 5):
        self._cache: Dict[str, CachedDocument] = {}
        self._ttl_minutes = ttl_minutes
        self._max_documents = max_documents
        self._cleanup_interval = cleanup_interval_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        # Don't start cleanup task in __init__ - wait for first use
    
    def _start_cleanup_task_if_needed(self):
        """Inicia task de limpeza automática se necessário e possível"""
        try:
            # Only start if there's a running event loop and task isn't already running
            if (self._cleanup_task is None or self._cleanup_task.done()) and len(self._cache) > 0:
                loop = asyncio.get_running_loop()
                self._cleanup_task = loop.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No running event loop - cleanup will be handled manually
            pass
    
    async def _periodic_cleanup(self):
        """Task periódica para limpeza de documentos expirados"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval * 60)  # Convert to seconds
                cleaned = await self.cleanup_expired()
                if cleaned > 0:
                    logger.info(f"DocumentCache: Cleaned {cleaned} expired documents")
            except asyncio.CancelledError:
                logger.info("DocumentCache: Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"DocumentCache: Error in periodic cleanup: {e}")
    
    def _generate_key(self) -> str:
        """Gera chave única para documento"""
        return str(uuid.uuid4())
    
    def _determine_file_type(self, filename: str) -> str:
        """Determina tipo de arquivo baseado na extensão"""
        if filename.lower().endswith('.pdf'):
            return 'pdf'
        elif filename.lower().endswith('.txt'):
            return 'txt'
        else:
            return 'unknown'
    
    def _calculate_text_stats(self, text_content: str) -> TextStats:
        """Calcula estatísticas do texto"""
        total_chars = len(text_content)
        total_words = len(text_content.split()) if text_content.strip() else 0
        total_lines = text_content.count('\n') + 1 if text_content else 0
        
        return TextStats(
            total_chars=total_chars,
            total_words=total_words,
            total_lines=total_lines
        )
    
    async def store_document(self, text_content: str, filename: str, file_size_bytes: int, processing_time_ms: float) -> str:
        """
        Armazena documento em cache e retorna chave única
        
        Args:
            text_content: Conteúdo de texto extraído do documento
            filename: Nome do arquivo original
            file_size_bytes: Tamanho do arquivo em bytes
            processing_time_ms: Tempo de processamento em milissegundos
            
        Returns:
            str: Chave única para acessar o documento
            
        Raises:
            ValueError: Se cache estiver cheio
        """
        # Verificar limite de documentos
        if len(self._cache) >= self._max_documents:
            # Tentar limpar expirados primeiro
            cleaned = await self.cleanup_expired()
            if len(self._cache) >= self._max_documents:
                raise ValueError(f"Cache full: maximum {self._max_documents} documents allowed")
        
        # Calcular estatísticas do texto
        text_stats = self._calculate_text_stats(text_content)
        
        # Gerar chave e criar documento
        key = self._generate_key()
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self._ttl_minutes)
        
        document = CachedDocument(
            key=key,
            filename=filename,
            text_content=text_content,
            file_type=self._determine_file_type(filename),
            file_size_bytes=file_size_bytes,
            text_stats=text_stats,
            processing_time_ms=processing_time_ms,
            created_at=now,
            last_accessed=now,
            expires_at=expires_at
        )
        
        self._cache[key] = document
        logger.info(f"DocumentCache: Stored document {filename} with key {key[:8]}...")
        
        # Start cleanup task if needed
        self._start_cleanup_task_if_needed()
        
        return key
    
    async def get_document(self, key: str) -> Optional[CachedDocument]:
        """
        Recupera documento do cache por chave
        
        Args:
            key: Chave do documento
            
        Returns:
            CachedDocument ou None se não encontrado/expirado
        """
        document = self._cache.get(key)
        
        if document is None:
            return None
        
        # Verificar se expirou
        if datetime.utcnow() > document.expires_at:
            await self.remove_document(key)
            return None
        
        # Atualizar last_accessed
        document.last_accessed = datetime.utcnow()
        
        return document
    
    async def remove_document(self, key: str) -> bool:
        """
        Remove documento do cache
        
        Args:
            key: Chave do documento
            
        Returns:
            bool: True se removido, False se não encontrado
        """
        if key in self._cache:
            document = self._cache.pop(key)
            logger.info(f"DocumentCache: Removed document {document.filename} with key {key[:8]}...")
            return True
        return False
    
    async def list_documents(self) -> List[DocumentInfo]:
        """
        Lista todos os documentos ativos no cache
        
        Returns:
            List[DocumentInfo]: Lista de informações dos documentos
        """
        # Limpar expirados primeiro
        await self.cleanup_expired()
        
        documents = []
        for doc in self._cache.values():
            documents.append(DocumentInfo(
                key=doc.key,
                filename=doc.filename,
                file_size_bytes=doc.file_size_bytes,
                text_stats=doc.text_stats,
                created_at=doc.created_at,
                expires_at=doc.expires_at,
                last_accessed=doc.last_accessed
            ))
        
        # Ordenar por data de criação (mais recente primeiro)
        documents.sort(key=lambda x: x.created_at, reverse=True)
        
        return documents
    
    async def cleanup_expired(self) -> int:
        """
        Remove documentos expirados do cache
        
        Returns:
            int: Número de documentos removidos
        """
        now = datetime.utcnow()
        expired_keys = []
        
        for key, document in self._cache.items():
            if now > document.expires_at:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self.remove_document(key)
        
        return len(expired_keys)
    
    async def get_cache_stats(self) -> Dict:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dict: Estatísticas de uso do cache
        """
        total_memory_bytes = sum(len(doc.text_content.encode('utf-8')) for doc in self._cache.values())
        total_file_size = sum(doc.file_size_bytes for doc in self._cache.values())
        
        return {
            "total_documents": len(self._cache),
            "max_documents": self._max_documents,
            "memory_usage_mb": round(total_memory_bytes / (1024 * 1024), 2),
            "total_file_size_mb": round(total_file_size / (1024 * 1024), 2),
            "ttl_minutes": self._ttl_minutes,
            "cleanup_interval_minutes": self._cleanup_interval
        }
    
    async def clear_all(self) -> int:
        """
        Remove todos os documentos do cache (para testes)
        
        Returns:
            int: Número de documentos removidos
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"DocumentCache: Cleared all {count} documents")
        return count
    
    def close(self):
        """Finaliza o serviço e cancela tasks"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# Singleton instance para uso global
_document_cache_service: Optional[DocumentCacheService] = None


def get_document_cache_service() -> DocumentCacheService:
    """Retorna instância singleton do DocumentCacheService"""
    global _document_cache_service
    if _document_cache_service is None:
        _document_cache_service = DocumentCacheService()
    return _document_cache_service


def close_document_cache_service():
    """Fecha o serviço de cache (para testes)"""
    global _document_cache_service
    if _document_cache_service is not None:
        _document_cache_service.close()
        _document_cache_service = None