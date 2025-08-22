# Local RAG com Python, LangChain e Neo4j

[![CI](https://github.com/roger8b/local_rag/actions/workflows/tests.yml/badge.svg)](https://github.com/roger8b/local_rag/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/roger8b/local_rag/branch/main/graph/badge.svg)](https://codecov.io/gh/roger8b/local_rag)

Sumário
- Documentação completa
- Guia rápido
- Observações

Este projeto implementa um sistema de Retrieval-Augmented Generation (RAG) local usando Python, LangChain e Neo4j. O sistema suporta múltiplos provedores de LLM (Ollama, OpenAI, Google Gemini) através de uma arquitetura flexível baseada no padrão Strategy.

Documentação completa
- Visão geral e arquitetura: docs/overview.md
- Arquitetura detalhada: docs/architecture.md
- Instalação e execução: docs/setup.md
- Configuração (.env e flags): docs/configuration.md
- Ingestão (API e pipeline): docs/ingestion.md
- Consulta (API): docs/query.md
- Limpeza do Neo4j: docs/neo4j_reset.md
- Troubleshooting: docs/troubleshooting.md

Guia rápido
1) Copie o exemplo de ambiente e ajuste as variáveis:
```
cp .env.example .env
```
2) Instale dependências e suba a API:
```
pip install -r requirements.txt
python run_api.py
```
3) Acesse http://localhost:8000/docs para usar:
- POST /api/v1/ingest (upload de .txt e .pdf)
- POST /api/v1/query
- GET /api/v1/models/{provider}
- POST /api/v1/schema/infer (inferência de schema de grafo)
- GET /api/v1/documents (Fase 6)
- DELETE /api/v1/documents/{doc_id} (Fase 6)

Observações
- **Provedores LLM**: Configure `LLM_PROVIDER` para `ollama` (padrão), `openai` ou `gemini`
- **Provedores Embedding**: Configure `EMBEDDING_PROVIDER` para `ollama` (padrão) ou `openai`
- Para provedores externos, defina as respectivas chaves de API: `OPENAI_API_KEY`, `GOOGLE_API_KEY`
- Em ambientes sem DB, use `NEO4J_VERIFY_CONNECTIVITY=false`

UI (Streamlit)
- Consulta (chat) e Upload
- Novo: Gerenciador de Documentos em `src/ui/pages/03_document_manager.py` (listar e remover documentos)

Notas sobre os badges:
- Repo público: badges já apontam para roger8b/local_rag.
- Codecov não requer token para repositórios públicos.
