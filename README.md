# Local RAG com Python, LangChain e Neo4j

![build](https://img.shields.io/badge/build-passing-brightgreen)
![tests](https://img.shields.io/badge/tests-68%20passed-brightgreen)

Este projeto implementa um sistema de Retrieval-Augmented Generation (RAG) local usando Python, LangChain e Neo4j.

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
- POST /api/v1/ingest (upload de .txt)
- POST /api/v1/query

Observações
- Para `embedding_provider=openai`, defina `OPENAI_API_KEY`.
- Em ambientes sem DB, use `NEO4J_VERIFY_CONNECTIVITY=false`.
