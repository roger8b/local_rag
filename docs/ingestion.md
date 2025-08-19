# Ingestão de Documentos

Endpoint
- `POST /api/v1/ingest`

Parâmetros (multipart/form-data)
- `file` (obrigatório): arquivo `.txt` ou `.pdf`
- `embedding_provider` (opcional): `ollama` (padrão) ou `openai`

Tipos de Arquivo Suportados
- **Arquivos de Texto (.txt)**: Processamento direto do conteúdo textual
- **Documentos PDF (.pdf)**: Extração de texto usando pypdf e processamento do conteúdo extraído

Comportamento
- Valida extensão (`.txt` ou `.pdf`)
- Extrai texto usando o loader apropriado (TextLoader para .txt, PDFLoader para .pdf)
- Faz chunking do conteúdo extraído
- Gera embeddings (Ollama por padrão; OpenAI se configurado)
- Persiste no Neo4j os nós `:Chunk` e relacionamentos sequenciais `(:Chunk)-[:NEXT]->(:Chunk)`
- Garante (se necessário) o índice vetorial `document_embeddings`

Notas
- Para `openai`, configure `OPENAI_API_KEY`
- Se o provedor de embeddings estiver indisponível, o sistema usa vetores zero como fallback (útil em dev)
- Quando `NEO4J_VERIFY_CONNECTIVITY=false` ou o DB está indisponível, a persistência é ignorada (modo degradado), mas o fluxo funciona

Exemplos cURL

**Upload de arquivo TXT com provider padrão:**

```bash
curl -s -S \
  -F "file=@example_document.txt;type=text/plain" \
  http://localhost:8000/api/v1/ingest
```

**Upload de arquivo PDF com OpenAI:**

```bash
curl -s -S \
  -F "file=@document.pdf;type=application/pdf" \
  -F "embedding_provider=openai" \
  http://localhost:8000/api/v1/ingest
```

**Upload especificando provider Ollama explicitamente:**

```bash
curl -s -S \
  -F "file=@document.txt;type=text/plain" \
  -F "embedding_provider=ollama" \
  http://localhost:8000/api/v1/ingest
```
