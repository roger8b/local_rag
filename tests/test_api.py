import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.main import app
from src.models.api_models import DocumentSource


client = TestClient(app)


class TestQueryEndpoint:
    
    def test_root_endpoint(self):
        """Test root endpoint returns expected response"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Local RAG API is running"
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_query_missing_question(self):
        """Test query endpoint with missing question field"""
        response = client.post("/api/v1/query", json={})
        assert response.status_code == 422
    
    def test_query_empty_question(self):
        """Test query endpoint with empty question"""
        response = client.post("/api/v1/query", json={"question": ""})
        assert response.status_code == 422
    
    @patch('src.retrieval.retriever.VectorRetriever.retrieve')
    @patch('src.generation.generator.ResponseGenerator.generate_response')
    @patch('src.retrieval.retriever.VectorRetriever.close')
    async def test_query_success(self, mock_close, mock_generate, mock_retrieve):
        """Test successful query with mocked dependencies"""
        # Mock retrieval results
        mock_sources = [
            DocumentSource(text="Test document content", score=0.95),
            DocumentSource(text="Another relevant document", score=0.87)
        ]
        mock_retrieve.return_value = mock_sources
        
        # Mock generation result
        mock_generate.return_value = "This is a test answer based on the documents."
        
        response = client.post("/api/v1/query", json={"question": "What is this about?"})
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "question" in data
        assert data["question"] == "What is this about?"
    
    @patch('src.retrieval.retriever.VectorRetriever.retrieve')
    @patch('src.retrieval.retriever.VectorRetriever.close')
    async def test_query_no_documents_found(self, mock_close, mock_retrieve):
        """Test query when no relevant documents are found"""
        mock_retrieve.return_value = []
        
        response = client.post("/api/v1/query", json={"question": "What is this about?"})
        
        assert response.status_code == 404
        assert "No relevant documents found" in response.json()["detail"]