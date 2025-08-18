import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.generation.generator import create_llm_provider, ResponseGenerator
from src.generation.providers.base import LLMProvider
from src.generation.providers.ollama import OllamaProvider
from src.generation.providers.openai import OpenAIProvider


class TestLLMProviderFactory:
    """Tests for the LLM provider factory function"""
    
    def test_create_ollama_provider(self):
        """Test that factory creates OllamaProvider when configured"""
        with patch('src.generation.generator.settings') as mock_settings:
            mock_settings.llm_provider = "ollama"
            provider = create_llm_provider()
            assert isinstance(provider, OllamaProvider)
    
    def test_create_openai_provider(self):
        """Test that factory creates OpenAIProvider when configured"""
        with patch('src.generation.generator.settings') as mock_settings, \
             patch('src.generation.providers.openai.settings') as mock_openai_settings:
            mock_settings.llm_provider = "openai"
            mock_openai_settings.openai_api_key = "test-key"
            mock_openai_settings.openai_model = "gpt-4o-mini"
            provider = create_llm_provider()
            assert isinstance(provider, OpenAIProvider)
    
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


class TestOpenAIProvider:
    """Tests for the OpenAIProvider class"""
    
    def test_openai_provider_initialization_success(self):
        """Test that OpenAIProvider initializes with correct settings"""
        with patch('src.generation.providers.openai.settings') as mock_settings, \
             patch('src.generation.providers.openai.openai.OpenAI') as mock_openai:
            
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_model = "gpt-4o-mini"
            
            provider = OpenAIProvider()
            assert provider.model == "gpt-4o-mini"
            mock_openai.assert_called_once_with(api_key="test-key")
    
    def test_openai_provider_initialization_no_api_key(self):
        """Test that OpenAIProvider fails without API key"""
        with patch('src.generation.providers.openai.settings') as mock_settings:
            mock_settings.openai_api_key = None
            
            with pytest.raises(ValueError) as exc_info:
                OpenAIProvider()
            
            assert "OPENAI_API_KEY é obrigatória" in str(exc_info.value)
    
    async def test_openai_provider_generate_response_success(self):
        """Test successful response generation with OpenAIProvider"""
        with patch('src.generation.providers.openai.settings') as mock_settings, \
             patch('src.generation.providers.openai.openai.OpenAI') as mock_openai_class:
            
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_model = "gpt-4o-mini"
            
            # Mock OpenAI client and response
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message = MagicMock()
            mock_response.choices[0].message.content = "Test response"
            
            mock_client.chat.completions.create.return_value = mock_response
            
            provider = OpenAIProvider()
            result = await provider.generate_response("Test question", [])
            
            assert result == "Test response"
            mock_client.chat.completions.create.assert_called_once()
    
    async def test_openai_provider_authentication_error(self):
        """Test OpenAI authentication error handling"""
        with patch('src.generation.providers.openai.settings') as mock_settings, \
             patch('src.generation.providers.openai.openai.OpenAI') as mock_openai_class:
            
            mock_settings.openai_api_key = "invalid-key"
            mock_settings.openai_model = "gpt-4o-mini"
            
            # Mock OpenAI client
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Import actual openai and create a proper AuthenticationError
            import openai
            mock_client.chat.completions.create.side_effect = openai.AuthenticationError(
                "Invalid API key", response=MagicMock(), body=MagicMock()
            )
            
            provider = OpenAIProvider()
            
            with pytest.raises(Exception) as exc_info:
                await provider.generate_response("Test question", [])
            
            assert "Erro de autenticação OpenAI" in str(exc_info.value)
    
    async def test_openai_provider_rate_limit_error(self):
        """Test OpenAI rate limit error handling"""
        with patch('src.generation.providers.openai.settings') as mock_settings, \
             patch('src.generation.providers.openai.openai.OpenAI') as mock_openai_class:
            
            mock_settings.openai_api_key = "test-key"
            mock_settings.openai_model = "gpt-4o-mini"
            
            # Mock OpenAI client
            mock_client = MagicMock()
            mock_openai_class.return_value = mock_client
            
            # Import actual openai and create a proper RateLimitError
            import openai
            mock_client.chat.completions.create.side_effect = openai.RateLimitError(
                "Rate limit exceeded", response=MagicMock(), body=MagicMock()
            )
            
            provider = OpenAIProvider()
            
            with pytest.raises(Exception) as exc_info:
                await provider.generate_response("Test question", [])
            
            assert "Erro de rate limit OpenAI" in str(exc_info.value)