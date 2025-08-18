import io
import sys
import builtins
from unittest.mock import patch, MagicMock


def _make_fake_driver(call_log):
    """Create a fake Neo4j driver/session that records run() queries into call_log."""
    fake_session = MagicMock()
    def run_side_effect(query, **params):
        call_log.append((query, params))
        # Return an object with .single() when SHOW INDEXES is called
        fake_result = MagicMock()
        # For SHOW INDEXES checks, simulate no existing index
        if query.strip().upper().startswith("SHOW INDEXES"):
            fake_result.single.return_value = None
        return fake_result

    fake_session.run.side_effect = run_side_effect
    fake_driver = MagicMock()
    fake_driver.session.return_value.__enter__.return_value = fake_session
    return fake_driver


def test_clear_database_aborts_without_confirmation(monkeypatch):
    from importlib import reload
    import scripts.clear_database as clear_db

    # Stub input to something other than 'yes'/'sim'
    monkeypatch.setattr(builtins, 'input', lambda _: 'nope')

    call_log = []
    fake_driver = _make_fake_driver(call_log)

    with patch('scripts.clear_database.GraphDatabase.driver', return_value=fake_driver):
        # Capture stdout
        stdout = io.StringIO()
        with patch('sys.stdout', stdout):
            clear_db.main()

    out = stdout.getvalue()
    assert 'Confirma a limpeza' in out
    # Ensure no destructive queries executed
    assert not any('DROP INDEX' in q for q, _ in call_log)
    assert not any('MATCH (n:Chunk) DETACH DELETE n' in q for q, _ in call_log)


def test_clear_database_executes_queries_on_confirmation(monkeypatch):
    from importlib import reload
    import scripts.clear_database as clear_db

    monkeypatch.setattr(builtins, 'input', lambda _: 'yes')

    call_log = []
    fake_driver = _make_fake_driver(call_log)

    with patch('scripts.clear_database.GraphDatabase.driver', return_value=fake_driver):
        stdout = io.StringIO()
        with patch('sys.stdout', stdout):
            clear_db.main()

    out = stdout.getvalue()
    assert "Conectando ao banco de dados" in out
    assert "Índice 'document_embeddings' removido" in out
    assert "Todos os nós :Chunk foram removidos" in out
    assert any('DROP INDEX document_embeddings IF EXISTS' in q for q, _ in call_log)
    assert any('MATCH (n:Chunk) DETACH DELETE n' in q for q, _ in call_log)


def test_after_clear_ingestion_recreates_index(monkeypatch):
    # Run clear script
    import scripts.clear_database as clear_db
    monkeypatch.setattr(builtins, 'input', lambda _: 'sim')

    call_log = []
    fake_driver = _make_fake_driver(call_log)

    with patch('scripts.clear_database.GraphDatabase.driver', return_value=fake_driver):
        clear_db.main()

    # Now perform a small ingestion and ensure index creation is attempted
    from src.application.services.ingestion_service import IngestionService
    # Patch the service to use our fake driver
    service = IngestionService()
    with patch.object(service, 'driver', fake_driver):
        # Avoid real HTTP by mocking embeddings
        with patch.object(service, '_generate_embeddings', return_value=[[0.0]*8]):
            # Small content -> 1 chunk is fine
            import asyncio
            asyncio.run(service.ingest_from_content("hello world", "test.txt"))

    # Expect SHOW INDEXES call then CREATE VECTOR INDEX in subsequent call
    joined = "\n".join(q for q,_ in call_log)
    assert "SHOW INDEXES" in joined
    assert "CREATE VECTOR INDEX document_embeddings" in joined

