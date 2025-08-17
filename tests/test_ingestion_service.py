
import pytest
from unittest.mock import patch, AsyncMock

from src.application.services.ingestion_service import IngestionService

# Mock para simular a resposta da API do Ollama
mock_ollama_response = {"embedding": [0.1] * 768}

# Mock para simular a resposta da API da OpenAI
mock_openai_response = {"data": [{"embedding": [0.2] * 1536}]} # OpenAI usa uma dimensão diferente

@pytest.fixture
def ingestion_service():
    """Fixture para criar uma instância do IngestionService para os testes."""
    with patch("src.application.services.ingestion_service.GraphDatabase.driver"):
        service = IngestionService()
        yield service
        service.close()

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_generate_embeddings_uses_ollama_by_default(mock_post, ingestion_service):
    """
    RED: Testa se o provedor 'ollama' é usado por padrão, chamando a URL correta.
    """
    mock_post.return_value.json.return_value = mock_ollama_response
    
    chunks = ["Este é um teste."]
    await ingestion_service._generate_embeddings(chunks, provider="ollama")
    
    mock_post.assert_called_once()
    called_url = mock_post.call_args[0][0]
    assert "localhost:11434/api/embeddings" in called_url # URL do Ollama

@pytest.mark.asyncio
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_generate_embeddings_uses_openai_when_specified(mock_post, ingestion_service):
    """
    RED: Testa se o provedor 'openai' é chamado quando especificado.
    Este teste falhará inicialmente porque a lógica para OpenAI não existe.
    """
    # Simula que a chave da OpenAI está configurada
    with patch("src.application.services.ingestion_service.settings.openai_api_key", "sk-test-key"):
        mock_post.return_value.json.return_value = mock_openai_response
        
        chunks = ["Este é um teste com OpenAI."]
        # Esta chamada deve falhar ou não se comportar como esperado
        await ingestion_service._generate_embeddings(chunks, provider="openai")
        
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        assert "api.openai.com/v1/embeddings" in called_url # URL da OpenAI

@pytest.mark.asyncio
async def test_generate_embeddings_raises_error_if_openai_key_is_missing(ingestion_service):
    """
    RED: Testa se um erro é levantado ao tentar usar OpenAI sem uma chave de API.
    """
    with patch("os.getenv", return_value=None): # Simula a falta da chave
        chunks = ["Teste sem chave."]
        with pytest.raises(ValueError, match="OPENAI_API_KEY não configurada"):
            await ingestion_service._generate_embeddings(chunks, provider="openai")

