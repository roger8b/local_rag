"""
Testes unitários para validação e funcionalidades do endpoint de schema inference
"""
import pytest
from pydantic import ValidationError
from src.models.api_models import SchemaInferRequest, SchemaInferResponse


class TestSchemaInferModels:
    """Testes para validação dos modelos Pydantic"""
    
    def test_schema_infer_request_valid(self):
        """Test que SchemaInferRequest aceita dados válidos"""
        request = SchemaInferRequest(
            text="João trabalha na empresa TechCorp",
            max_sample_length=1000
        )
        
        assert request.text == "João trabalha na empresa TechCorp"
        assert request.max_sample_length == 1000
    
    def test_schema_infer_request_default_max_length(self):
        """Test que max_sample_length tem valor padrão 500"""
        request = SchemaInferRequest(text="Test text")
        
        assert request.max_sample_length == 500
    
    def test_schema_infer_request_text_required(self):
        """Test que campo text é obrigatório"""
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferRequest()
        
        errors = exc_info.value.errors()
        text_error = next((e for e in errors if e["loc"] == ("text",)), None)
        assert text_error is not None
        assert text_error["type"] == "missing"
    
    def test_schema_infer_request_empty_text_invalid(self):
        """Test que texto vazio é inválido"""
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferRequest(text="")
        
        errors = exc_info.value.errors()
        text_error = next((e for e in errors if e["loc"] == ("text",)), None)
        assert text_error is not None
        assert "at least 1 character" in str(text_error["msg"])
    
    def test_schema_infer_request_max_length_bounds(self):
        """Test validação dos limites de max_sample_length"""
        # Valor muito baixo
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferRequest(text="Test", max_sample_length=10)
        
        errors = exc_info.value.errors()
        length_error = next((e for e in errors if e["loc"] == ("max_sample_length",)), None)
        assert length_error is not None
        assert "greater than or equal to 50" in str(length_error["msg"])
        
        # Valor muito alto
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferRequest(text="Test", max_sample_length=5000)
        
        errors = exc_info.value.errors()
        length_error = next((e for e in errors if e["loc"] == ("max_sample_length",)), None)
        assert length_error is not None
        assert "less than or equal to 2000" in str(length_error["msg"])
    
    def test_schema_infer_request_valid_bounds(self):
        """Test que valores nos limites são aceitos"""
        # Limite mínimo
        request_min = SchemaInferRequest(text="Test", max_sample_length=50)
        assert request_min.max_sample_length == 50
        
        # Limite máximo
        request_max = SchemaInferRequest(text="Test", max_sample_length=2000)
        assert request_max.max_sample_length == 2000
    
    def test_schema_infer_response_llm_source(self):
        """Test criação de resposta com fonte LLM"""
        response = SchemaInferResponse(
            node_labels=["Person", "Company"],
            relationship_types=["WORKS_AT"],
            source="llm",
            model_used="qwen3:8b",
            processing_time_ms=1250.5
        )
        
        assert response.node_labels == ["Person", "Company"]
        assert response.relationship_types == ["WORKS_AT"]
        assert response.source == "llm"
        assert response.model_used == "qwen3:8b"
        assert response.processing_time_ms == 1250.5
        assert response.reason is None
    
    def test_schema_infer_response_fallback_source(self):
        """Test criação de resposta com fonte fallback"""
        response = SchemaInferResponse(
            node_labels=["Entity", "Concept"],
            relationship_types=["RELATED_TO", "MENTIONS"],
            source="fallback",
            model_used=None,
            processing_time_ms=15.2,
            reason="Ollama service unavailable"
        )
        
        assert response.source == "fallback"
        assert response.model_used is None
        assert response.reason == "Ollama service unavailable"
    
    def test_schema_infer_response_invalid_source(self):
        """Test que fonte inválida gera erro"""
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferResponse(
                node_labels=["Test"],
                relationship_types=["TEST"],
                source="invalid_source",  # Deve ser "llm" ou "fallback"
                processing_time_ms=100.0
            )
        
        errors = exc_info.value.errors()
        source_error = next((e for e in errors if e["loc"] == ("source",)), None)
        assert source_error is not None
    
    def test_schema_infer_response_required_fields(self):
        """Test que campos obrigatórios são validados"""
        # Teste sem node_labels
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferResponse(
                relationship_types=["TEST"],
                source="llm",
                processing_time_ms=100.0
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("node_labels",) for e in errors)
        
        # Teste sem relationship_types
        with pytest.raises(ValidationError) as exc_info:
            SchemaInferResponse(
                node_labels=["Test"],
                source="llm",
                processing_time_ms=100.0
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("relationship_types",) for e in errors)
    
    def test_schema_infer_response_empty_lists_allowed(self):
        """Test que listas vazias são permitidas"""
        response = SchemaInferResponse(
            node_labels=[],
            relationship_types=[],
            source="fallback",
            processing_time_ms=50.0,
            reason="No schema could be inferred"
        )
        
        assert response.node_labels == []
        assert response.relationship_types == []
    
    def test_schema_infer_models_json_serialization(self):
        """Test que modelos podem ser serializados para JSON"""
        request = SchemaInferRequest(
            text="Test serialization",
            max_sample_length=1000
        )
        
        response = SchemaInferResponse(
            node_labels=["Person", "Company"],
            relationship_types=["WORKS_AT"],
            source="llm",
            model_used="qwen3:8b",
            processing_time_ms=1250.5
        )
        
        # Test serialization
        request_json = request.model_dump()
        response_json = response.model_dump()
        
        assert isinstance(request_json, dict)
        assert isinstance(response_json, dict)
        assert "text" in request_json
        assert "node_labels" in response_json
    
    def test_schema_infer_request_extra_fields_ignored(self):
        """Test que campos extras são ignorados"""
        # Pydantic deve ignorar campos extras por padrão
        request_data = {
            "text": "Test text",
            "max_sample_length": 500,
            "extra_field": "should be ignored"
        }
        
        request = SchemaInferRequest(**request_data)
        assert request.text == "Test text"
        assert request.max_sample_length == 500
        assert not hasattr(request, "extra_field")


class TestSchemaInferenceLogic:
    """Testes para lógica de inferência de schema"""
    
    def test_fallback_detection_logic(self):
        """Test lógica de detecção de fallback schema"""
        # Simular a lógica usada no endpoint
        schema_result = {
            "node_labels": ["Entity", "Concept"],
            "relationship_types": ["RELATED_TO", "MENTIONS"]
        }
        
        is_fallback = (
            schema_result.get("node_labels") == ["Entity", "Concept"] and 
            schema_result.get("relationship_types") == ["RELATED_TO", "MENTIONS"]
        )
        
        assert is_fallback is True
        
        # Teste com schema não-fallback
        schema_result_llm = {
            "node_labels": ["Person", "Company"],
            "relationship_types": ["WORKS_AT"]
        }
        
        is_fallback_llm = (
            schema_result_llm.get("node_labels") == ["Entity", "Concept"] and 
            schema_result_llm.get("relationship_types") == ["RELATED_TO", "MENTIONS"]
        )
        
        assert is_fallback_llm is False
    
    def test_text_truncation_logic(self):
        """Test lógica de truncagem de texto"""
        original_text = "A" * 1000
        max_length = 500
        
        # Simular lógica do endpoint
        truncated = original_text[:max_length] if len(original_text) > max_length else original_text
        
        assert len(truncated) == max_length
        assert truncated == "A" * 500
        
        # Teste com texto menor que limite
        short_text = "A" * 100
        truncated_short = short_text[:max_length] if len(short_text) > max_length else short_text
        
        assert len(truncated_short) == 100
        assert truncated_short == short_text