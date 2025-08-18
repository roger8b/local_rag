import pytest
from unittest.mock import patch, MagicMock
from src.generation.generator import create_llm_provider, ResponseGenerator
from src.generation.providers.base import LLMProvider
from src.generation.providers.ollama import OllamaProvider


class TestLLMProviderFactory:
    """Tests for the LLM provider factory function"""
    
    def test_create_ollama_provider(self):
        """Test that factory creates OllamaProvider when configured"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "ollama"
            provider = create_llm_provider()
            assert isinstance(provider, OllamaProvider)
    
    def test_create_openai_provider_not_implemented(self):
        """Test that factory raises NotImplementedError for OpenAI"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "openai"
            with pytest.raises(NotImplementedError) as exc_info:
                create_llm_provider()
            assert "não suportado ainda" in str(exc_info.value)
    
    def test_create_gemini_provider_not_implemented(self):
        """Test that factory raises NotImplementedError for Gemini"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "gemini"
            with pytest.raises(NotImplementedError) as exc_info:
                create_llm_provider()
            assert "não suportado ainda" in str(exc_info.value)
    
    def test_create_invalid_provider(self):
        """Test that factory raises ValueError for invalid provider"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "anthropic"
            with pytest.raises(ValueError) as exc_info:
                create_llm_provider()
            assert "não suportado" in str(exc_info.value)
    
    def test_case_insensitive_provider_name(self):
        """Test that provider names are case insensitive"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "OLLAMA"
            provider = create_llm_provider()
            assert isinstance(provider, OllamaProvider)


class TestResponseGenerator:
    """Tests for the ResponseGenerator class"""
    
    @patch('src.generation.generator.create_llm_provider')
    def test_response_generator_initialization(self, mock_create_provider):
        """Test that ResponseGenerator initializes with the correct provider"""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_create_provider.return_value = mock_provider
        
        generator = ResponseGenerator()
        assert generator.provider == mock_provider
        mock_create_provider.assert_called_once()
    
    @patch('src.generation.generator.create_llm_provider')
    async def test_generate_response_delegates_to_provider(self, mock_create_provider):
        """Test that generate_response delegates to the provider"""
        mock_provider = MagicMock(spec=LLMProvider)
        mock_provider.generate_response.return_value = "Test response"
        mock_create_provider.return_value = mock_provider
        
        generator = ResponseGenerator()
        
        question = "Test question"
        sources = []
        
        result = await generator.generate_response(question, sources)
        
        assert result == "Test response"
        mock_provider.generate_response.assert_called_once_with(question, sources)


class TestOllamaProvider:
    """Tests for the OllamaProvider class"""
    
    def test_ollama_provider_initialization(self):
        """Test that OllamaProvider initializes with correct settings"""
        with patch('src.generation.providers.ollama.settings') as mock_settings:
            mock_settings.ollama_base_url = "http://test:11434"
            mock_settings.llm_model = "test-model"
            
            provider = OllamaProvider()
            assert provider.base_url == "http://test:11434"
            assert provider.model == "test-model"
    
    async def test_ollama_provider_generate_response_success(self):
        """Test successful response generation with OllamaProvider"""
        with patch('src.generation.providers.ollama.settings') as mock_settings, \
             patch('src.generation.providers.ollama.httpx.AsyncClient') as mock_client:
            
            mock_settings.ollama_base_url = "http://test:11434"
            mock_settings.llm_model = "test-model"
            
            # Mock the HTTP response
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "Test response"}
            mock_response.raise_for_status = MagicMock()
            
            # Create async mock for post method
            from unittest.mock import AsyncMock
            mock_client_instance = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            provider = OllamaProvider()
            result = await provider.generate_response("Test question", [])
            
            assert result == "Test response"
            mock_client_instance.post.assert_called_once()
    
    async def test_ollama_provider_generate_response_error(self):
        """Test error handling in OllamaProvider"""
        with patch('src.generation.providers.ollama.settings') as mock_settings, \
             patch('src.generation.providers.ollama.httpx.AsyncClient') as mock_client:
            
            mock_settings.ollama_base_url = "http://test:11434"
            mock_settings.llm_model = "test-model"
            
            # Mock HTTP error
            mock_client_instance = MagicMock()
            mock_client_instance.post.side_effect = Exception("Connection error")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            provider = OllamaProvider()
            
            with pytest.raises(Exception) as exc_info:
                await provider.generate_response("Test question", [])
            
            assert "Error generating response with Ollama" in str(exc_info.value)