"""
Testes de integração para o endpoint GET /api/v1/models/{provider}
Seguindo metodologia TDD para Fase 5.1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from src.main import app


class TestModelsEndpoint:
    """Testes para endpoint de listagem de modelos por provider"""
    
    def test_models_endpoint_not_implemented_yet(self):
        """
        AC 1: Test que endpoint GET /api/v1/models/{provider} existe.
        Para ser determinístico no CI (sem Ollama real), mockamos a chamada HTTP
        para retornar 200 e uma lista válida de modelos.
        """
        with patch('src.api.routes.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"models": [{"name": "qwen3:8b"}]}
            mock_response.raise_for_status = MagicMock()

            async def mock_get(*args, **kwargs):
                return mock_response

            mock_client.get = mock_get

            client = TestClient(app)
            response = client.get("/api/v1/models/ollama")

            assert response.status_code == 200
    
    def test_ollama_models_list(self):
        """
        AC 2: Test que endpoint retorna lista de modelos do Ollama
        """
        with patch('src.api.routes.httpx.AsyncClient') as mock_client_class:
            # Mock do AsyncClient e seu context manager
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock resposta do Ollama API - usar valores síncronos
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models": [
                    {"name": "qwen3:8b", "size": 4800000000},
                    {"name": "llama2:13b", "size": 7300000000}
                ]
            }
            mock_response.raise_for_status = Mock()
            
            # O get deve retornar o mock_response que será await
            async def mock_get(*args, **kwargs):
                return mock_response
            
            mock_client.get = mock_get
            
            client = TestClient(app)
            response = client.get("/api/v1/models/ollama")
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
            assert response.status_code == 200
            data = response.json()
            print(f"Response data: {data}")
            assert "models" in data
            assert "default" in data
            assert isinstance(data["models"], list)
            assert len(data["models"]) >= 1
            assert data["default"] == "qwen3:8b"  # Configured default
    
    def test_openai_models_list(self):
        """
        AC 3: Test que endpoint retorna lista de modelos do OpenAI
        """
        client = TestClient(app)
        response = client.get("/api/v1/models/openai")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default" in data
        assert isinstance(data["models"], list)
        
        # OpenAI deve retornar lista estática configurada
        expected_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        for model in expected_models:
            assert model in data["models"]
        
        assert data["default"] == "gpt-4o-mini"
    
    def test_gemini_models_list(self):
        """
        AC 4: Test que endpoint retorna lista de modelos do Gemini
        """
        client = TestClient(app)
        response = client.get("/api/v1/models/gemini")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "default" in data
        assert isinstance(data["models"], list)
        
        # Gemini deve retornar lista estática configurada
        expected_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
        for model in expected_models:
            assert model in data["models"]
        
        assert data["default"] == "gemini-2.0-flash-exp"
    
    def test_invalid_provider_error(self):
        """
        Test que provider inválido retorna erro 422
        """
        client = TestClient(app)
        response = client.get("/api/v1/models/invalid_provider")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Invalid provider" in data["detail"]
    
    def test_ollama_offline_graceful_error(self):
        """
        Test que erro do Ollama offline é tratado graciosamente
        """
        with patch('src.api.routes.httpx.AsyncClient') as mock_client_class:
            # Mock HTTP error using the same pattern as other tests
            mock_client_instance = MagicMock()
            mock_client_instance.get.side_effect = Exception("Connection refused")
            mock_client_class.return_value.__aenter__.return_value = mock_client_instance
            
            client = TestClient(app)
            response = client.get("/api/v1/models/ollama")
            
            assert response.status_code == 503  # Service Unavailable
            data = response.json()
            assert "detail" in data
            assert "Ollama" in data["detail"]
            assert "unavailable" in data["detail"].lower()
