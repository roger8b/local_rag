# Configuração (.env e flags)

## Provedores LLM e Embedding

O sistema suporta múltiplos provedores através de uma arquitetura flexível:

### Configuração de Provedores
- `LLM_PROVIDER` (default: ollama): provedor para geração de respostas (`ollama`, `openai`, `gemini`)
- `EMBEDDING_PROVIDER` (default: ollama): provedor para embeddings (`ollama`, `openai`)

### Variáveis por Provedor

**Neo4j**
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: credenciais do Neo4j
- `NEO4J_VERIFY_CONNECTIVITY` (default: true): valida conectividade do Neo4j na inicialização; defina `false` para pular em ambientes sem DB

**Ollama** (provedor local padrão)
- `OLLAMA_BASE_URL` (default: http://localhost:11434)
- `EMBEDDING_MODEL` (default: nomic-embed-text)
- `LLM_MODEL` (default: qwen3:8b)

**OpenAI** (provedor externo opcional)
- `OPENAI_API_KEY`: chave da API da OpenAI (obrigatória se usar OpenAI)
- `OPENAI_MODEL` (default: gpt-4o-mini): modelo de LLM a usar
- `OPENAI_EMBEDDING_MODEL` (default: text-embedding-3-small): modelo de embedding a usar
- `OPENAI_EMBEDDING_DIMENSIONS` (default: 768): dimensão dos embeddings e usada na criação do índice vetorial

**Google Gemini** (provedor externo - em desenvolvimento)
- `GOOGLE_API_KEY`: chave da API do Google (será implementada na próxima versão)
- `GOOGLE_MODEL` (default: gemini-2.0-flash-exp): modelo Gemini a usar

**API**
- `API_HOST`, `API_PORT` (default: 0.0.0.0:8000)

## Exemplo Completo de .env

```bash
# Configuração de Provedores
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_VERIFY_CONNECTIVITY=true

# Ollama (provedor local padrão)
OLLAMA_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=nomic-embed-text
LLM_MODEL=qwen3:8b

# OpenAI (descomente para usar)
# LLM_PROVIDER=openai
# EMBEDDING_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSIONS=768

# Google Gemini (futuro)
# LLM_PROVIDER=gemini
# GOOGLE_API_KEY=your-google-key-here
GOOGLE_MODEL=gemini-2.0-flash-exp

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## Cenários de Uso

**Desenvolvimento Local (padrão)**
```bash
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
```

**Produção com OpenAI**
```bash
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

**Híbrido (LLM externo + Embedding local)**
```bash
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=ollama
OPENAI_API_KEY=sk-your-key-here
```
