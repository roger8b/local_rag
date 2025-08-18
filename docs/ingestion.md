# Ingestão de Documentos

Endpoint
- `POST /api/v1/ingest`

Parâmetros (multipart/form-data)
- `file` (obrigatório): arquivo `.txt`
- `embedding_provider` (opcional): `ollama` (padrão) ou `openai`

Comportamento
- Valida extensão `.txt`
- Faz chunking do conteúdo
- Gera embeddings (Ollama por padrão; OpenAI se configurado)
- Persiste no Neo4j os nós `:Chunk` e relacionamentos sequenciais `(:Chunk)-[:NEXT]->(:Chunk)`
- Garante (se necessário) o índice vetorial `document_embeddings`

Notas
- Para `openai`, configure `OPENAI_API_KEY`
- Se o provedor de embeddings estiver indisponível, o sistema usa vetores zero como fallback (útil em dev)
- Quando `NEO4J_VERIFY_CONNECTIVITY=false` ou o DB está indisponível, a persistência é ignorada (modo degradado), mas o fluxo funciona

Exemplo cURL
```
curl -s -S \
  -F "file=@example_document.txt;type=text/plain" \
  -F "embedding_provider=ollama" \
  http://localhost:8000/api/v1/ingest
```
