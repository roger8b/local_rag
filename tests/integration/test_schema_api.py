"""
Testes de integração para o endpoint POST /api/v1/schema/infer
Seguindo metodologia TDD para História 6: API para Inferência de Schema de Grafo
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from src.main import app


class TestSchemaInferEndpoint:
    """Testes para endpoint de inferência de schema de grafo"""
    
    def test_schema_infer_endpoint_exists(self):
        """
        AC 1: Test que endpoint POST /api/v1/schema/infer existe
        """
        client = TestClient(app)
        response = client.post(
            "/api/v1/schema/infer",
            json={"text": "Test text for schema inference"}
        )
        
        # Deve responder com status diferente de 404
        assert response.status_code != 404
    
    def test_schema_infer_with_valid_text(self):
        """
        AC 1: Test que endpoint retorna schema válido com texto de entrada
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            # Mock schema inference response
            mock_infer.return_value = {
                "node_labels": ["Person", "Company", "Technology"],
                "relationship_types": ["WORKS_AT", "USES", "DEVELOPS"]
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={
                    "text": "João Silva trabalha na empresa TechCorp desenvolvendo aplicações com React.",
                    "max_sample_length": 1000
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificar estrutura da resposta
            assert "node_labels" in data
            assert "relationship_types" in data
            assert "source" in data
            assert "processing_time_ms" in data
            
            # Verificar conteúdo
            assert data["node_labels"] == ["Person", "Company", "Technology"]
            assert data["relationship_types"] == ["WORKS_AT", "USES", "DEVELOPS"]
            assert data["source"] == "llm"
            assert isinstance(data["processing_time_ms"], (int, float))
    
    def test_schema_infer_validation_empty_text(self):
        """
        AC 2: Test que texto vazio retorna erro 422
        """
        client = TestClient(app)
        response = client.post(
            "/api/v1/schema/infer",
            json={"text": ""}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_schema_infer_validation_missing_text(self):
        """
        AC 2: Test que request sem campo text retorna erro 422
        """
        client = TestClient(app)
        response = client.post(
            "/api/v1/schema/infer",
            json={}
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_schema_infer_fallback_response(self):
        """
        AC 3: Test que retorna schema fallback quando LLM não disponível
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            # Mock fallback response (what the function returns when Ollama is unavailable)
            mock_infer.return_value = {
                "node_labels": ["Entity", "Concept"],
                "relationship_types": ["RELATED_TO", "MENTIONS"]
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={"text": "Some sample text for analysis"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificar que é reconhecido como fallback
            assert data["source"] == "fallback"
            assert data["node_labels"] == ["Entity", "Concept"]
            assert data["relationship_types"] == ["RELATED_TO", "MENTIONS"]
            assert data["model_used"] is None
            assert "reason" in data
    
    def test_schema_infer_response_structure(self):
        """
        AC 4: Test que resposta tem estrutura correta
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Document", "Section"],
                "relationship_types": ["CONTAINS", "REFERENCES"]
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={"text": "Document with multiple sections and references"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificar todos os campos obrigatórios
            required_fields = [
                "node_labels", "relationship_types", "source", 
                "processing_time_ms"
            ]
            for field in required_fields:
                assert field in data
            
            # Verificar tipos
            assert isinstance(data["node_labels"], list)
            assert isinstance(data["relationship_types"], list)
            assert data["source"] in ["llm", "fallback"]
            assert isinstance(data["processing_time_ms"], (int, float))
    
    def test_schema_infer_max_sample_length(self):
        """
        Test que max_sample_length é respeitado
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Text"],
                "relationship_types": ["CONTAINS"]
            }
            
            # Texto longo que deve ser truncado
            long_text = "A" * 1000
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={
                    "text": long_text,
                    "max_sample_length": 100
                }
            )
            
            assert response.status_code == 200
            
            # Verificar que o mock foi chamado com texto truncado
            mock_infer.assert_called_once()
            called_text = mock_infer.call_args[0][0]
            assert len(called_text) == 100
    
    def test_schema_infer_validation_max_sample_length_bounds(self):
        """
        Test validação dos limites de max_sample_length
        """
        client = TestClient(app)
        
        # Testar valor muito baixo
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "text": "Test text",
                "max_sample_length": 10  # Menor que mínimo (50)
            }
        )
        assert response.status_code == 422
        
        # Testar valor muito alto
        response = client.post(
            "/api/v1/schema/infer",
            json={
                "text": "Test text",
                "max_sample_length": 5000  # Maior que máximo (2000)
            }
        )
        assert response.status_code == 422
    
    def test_schema_infer_default_max_sample_length(self):
        """
        Test que max_sample_length padrão é 500
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            mock_infer.return_value = {
                "node_labels": ["Default"],
                "relationship_types": ["TEST"]
            }
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={"text": "A" * 600}  # Texto maior que padrão
            )
            
            assert response.status_code == 200
            
            # Verificar que foi truncado para 500 (padrão)
            mock_infer.assert_called_once()
            called_text = mock_infer.call_args[0][0]
            assert len(called_text) == 500
    
    def test_schema_infer_error_handling(self):
        """
        Test que erros são tratados e retornam fallback
        """
        with patch('src.application.services.ingestion_service.IngestionService._infer_graph_schema') as mock_infer:
            # Mock uma exceção
            mock_infer.side_effect = Exception("Simulated error")
            
            client = TestClient(app)
            response = client.post(
                "/api/v1/schema/infer",
                json={"text": "Test text for error scenario"}
            )
            
            # Deve retornar schema fallback ao invés de falhar
            assert response.status_code == 200
            data = response.json()
            
            assert data["source"] == "fallback"
            assert data["node_labels"] == ["Entity", "Concept"]
            assert data["relationship_types"] == ["RELATED_TO", "MENTIONS"]
            assert "Error during processing" in data["reason"]