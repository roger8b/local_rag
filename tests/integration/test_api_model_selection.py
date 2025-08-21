"""
Testes de integração para seleção de modelo específico nos endpoints
Seguindo metodologia TDD para Fase 5.1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app


class TestModelSelectionEndpoints:
    """Testes para seleção de modelo específico via API"""
    
    def test_query_with_specific_model(self):
        """
        AC 3: Test que endpoint query aceita provider e model_name
        """
        with patch('src.retrieval.retriever.VectorRetriever.retrieve') as mock_retrieve, \
             patch('src.generation.generator.ResponseGenerator.generate_response') as mock_generate, \
             patch('src.generation.generator.ResponseGenerator.get_provider_name') as mock_provider_name:
            
            # Mock retrieval and generation
            from src.models.api_models import DocumentSource
            mock_retrieve.return_value = [
                DocumentSource(text="Test document", score=0.95)
            ]
            mock_generate.return_value = "Test response from specific model"
            mock_provider_name.return_value = "openai"
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/query",
                json={
                    "question": "Test question",
                    "provider": "openai", 
                    "model_name": "gpt-4o-mini"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test response from specific model"
            assert data["provider_used"] == "openai"
    
    def test_ingest_with_specific_model(self):
        """
        Test que endpoint ingest aceita embedding_provider e model_name
        """
        with patch('src.application.services.ingestion_service.GraphDatabase'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock das respostas HTTP para embeddings
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            client = TestClient(app)
            txt_content = b"Test content for specific model"
            files = {"file": ("test.txt", txt_content, "text/plain")}
            data = {
                "embedding_provider": "ollama",
                "model_name": "nomic-embed-text"
            }
            
            response = client.post(
                "/api/v1/ingest",
                files=files,
                data=data
            )
            
            assert response.status_code == 201
            result = response.json()
            assert result["status"] == "success"
            assert result["filename"] == "test.txt"
    
    def test_models_endpoint_ollama_success(self):
        """
        AC 2: Test que endpoint models/ollama funciona corretamente
        """
        # Vou remover este teste duplicado já que ele já existe no test_api_models_endpoint.py
        # e usar apenas os testes específicos de seleção de modelo
        pass
    
    def test_query_without_model_uses_default(self):
        """
        Test que query sem model_name usa modelo padrão
        """
        with patch('src.retrieval.retriever.VectorRetriever.retrieve') as mock_retrieve, \
             patch('src.generation.generator.ResponseGenerator.generate_response') as mock_generate, \
             patch('src.generation.generator.ResponseGenerator.get_provider_name') as mock_provider_name:
            
            # Mock retrieval and generation
            from src.models.api_models import DocumentSource
            mock_retrieve.return_value = [
                DocumentSource(text="Test document", score=0.95)
            ]
            mock_generate.return_value = "Test response from default model"
            mock_provider_name.return_value = "ollama"
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/query",
                json={
                    "question": "Test question",
                    "provider": "ollama"
                    # No model_name specified, should use default
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test response from default model"