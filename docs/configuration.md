# Configuração (.env e flags)

Variáveis principais
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: credenciais do Neo4j
- `NEO4J_VERIFY_CONNECTIVITY` (default: true): valida conectividade do Neo4j na inicialização; defina `false` para pular em ambientes sem DB
- `OLLAMA_BASE_URL` (default: http://localhost:11434)
- `EMBEDDING_MODEL` (default: nomic-embed-text)
- `LLM_MODEL` (default: qwen3:8b)
- `OPENAI_API_KEY` (opcional): habilita embeddings via OpenAI
- `OPENAI_EMBEDDING_DIMENSIONS` (default: 768): dimensão dos embeddings ao usar OpenAI e usada na criação do índice vetorial
- `API_HOST`, `API_PORT` (default: 0.0.0.0:8000)

Exemplo
```
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_VERIFY_CONNECTIVITY=true

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=qwen3:8b

# OpenAI
OPENAI_API_KEY=
OPENAI_EMBEDDING_DIMENSIONS=768

# API
API_HOST=0.0.0.0
API_PORT=8000
```
