"""
Testes para a API de Administração (ex: limpeza de banco)
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app  # Importa a instância principal do FastAPI

# Usar um cliente de teste para toda a sessão de testes
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_clear_database_endpoint(client: TestClient):
    """Testa a limpeza completa do banco de dados através do endpoint de API."""
    # Passo 1: Garantir que há dados no banco (ingerir um documento)
    test_content = "Este é um documento de teste para a limpeza da base.".encode('utf-8')
    response_ingest = client.post(
        "/api/v1/ingest",
        files={"file": ("test_clear.txt", test_content, "text/plain")},
        data={"embedding_provider": "ollama"} # Usar ollama para não depender de chaves de API
    )
    assert response_ingest.status_code == 201
    ingest_data = response_ingest.json()
    assert ingest_data["chunks_created"] > 0

    # Verificar o status para confirmar que os dados existem
    response_status_before = client.get("/api/v1/db/status")
    assert response_status_before.status_code == 200
    status_before = response_status_before.json()
    assert status_before["chunks"] > 0

    # Passo 2: Chamar o endpoint de limpeza
    response_clear = client.delete("/api/v1/db/clear")
    assert response_clear.status_code == 200
    clear_data = response_clear.json()
    assert clear_data["status"] == "success"

    # Passo 3: Verificar se o banco de dados está vazio
    response_status_after = client.get("/api/v1/db/status")
    assert response_status_after.status_code == 200
    status_after = response_status_after.json()
    assert status_after["chunks"] == 0
    assert status_after["documents"] == 0 # O endpoint agora deve apagar documentos também
