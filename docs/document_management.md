# Document Management System - Histórias 7 & 8

## Visão Geral

O sistema de gerenciamento de documentos permite upload seguro, cache em memória e inferência de schema de grafos com controle avançado. Implementado nas **História 7** e **História 8**.

## Funcionalidades

### 📤 Upload Seguro (História 7)
- Upload de arquivos via multipart/form-data
- Suporte a formatos: `.txt`, `.pdf`
- Extração automática de texto
- Geração de chaves UUID únicas
- Cache em memória com TTL configurável (30min)
- Limpeza automática de documentos expirados

### 📊 Estatísticas Detalhadas (História 8)
- **Tamanho do arquivo** original (bytes)
- **Estatísticas do texto** extraído:
  - Total de caracteres
  - Total de palavras  
  - Total de linhas
- **Tempo de processamento** do upload
- **Informações de expiração** (created_at, expires_at)

### 🎛️ Controle de Inferência (História 8)
- **Seleção de modelo LLM** no endpoint de inferência
- **Controle por percentual** (0-100%) para amostragem de texto
- **Backward compatibility** com max_sample_length absoluto
- **Provider override** em runtime

## API Endpoints

### POST /api/v1/schema/upload
Upload de documento para análise posterior.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/schema/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "key": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "file_size_bytes": 1048576,
  "text_stats": {
    "total_chars": 15847,
    "total_words": 2341,
    "total_lines": 156
  },
  "processing_time_ms": 234.5,
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-15T11:00:00Z",
  "file_type": "pdf"
}
```

### POST /api/v1/schema/infer
Inferência de schema usando documento cacheado ou texto direto.

**Request com Controle por Percentual:**
```bash
curl -X POST "http://localhost:8000/api/v1/schema/infer" \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "sample_percentage": 30,
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini"
  }'
```

**Response:**
```json
{
  "node_labels": ["Person", "Company", "Technology"],
  "relationship_types": ["WORKS_AT", "USES", "DEVELOPS"],
  "source": "llm",
  "model_used": "openai:gpt-4o-mini",
  "processing_time_ms": 1250.5,
  "document_info": {
    "filename": "document.pdf",
    "sample_percentage": 30.0,
    "sample_size": 4754,
    "total_size": 15847
  }
}
```

### GET /api/v1/schema/documents
Listar todos os documentos em cache.

**Response:**
```json
{
  "documents": [
    {
      "key": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "file_size_bytes": 1048576,
      "text_stats": {
        "total_chars": 15847,
        "total_words": 2341,
        "total_lines": 156
      },
      "created_at": "2025-01-15T10:30:00Z",
      "expires_at": "2025-01-15T11:00:00Z",
      "last_accessed": "2025-01-15T10:35:00Z"
    }
  ],
  "total_documents": 1,
  "memory_usage_mb": 15.2,
  "total_file_size_mb": 1.0,
  "max_documents": 100,
  "ttl_minutes": 30
}
```

### DELETE /api/v1/schema/documents/{key}
Remover documento específico do cache.

## Lógica de Amostragem

### Controle por Percentual (História 8)
```python
# Exemplos de amostragem
sample_percentage = 25  # 25% do documento
if document_has_10000_chars:
    sample_size = 2500  # 25% de 10.000 = 2.500 caracteres

# Tamanho mínimo garantido
if calculated_size < 50:
    sample_size = min(50, total_document_length)
```

### Backward Compatibility
```python
# Lógica de prioridade
if max_sample_length is not None:
    sample_size = max_sample_length  # Usa valor absoluto
elif sample_percentage == 50 and max_sample_length is None:
    sample_size = 500  # Default para compatibilidade
else:
    sample_size = int(total_chars * sample_percentage / 100)
    sample_size = max(sample_size, 50)  # Mínimo 50 caracteres
```

## Sistema de Cache

### Configurações
```python
MAX_DOCUMENTS = 100        # Máximo de documentos em cache
TTL_MINUTES = 30           # Tempo de vida em minutos
CLEANUP_INTERVAL = 300     # Limpeza a cada 5 minutos
```

### Características
- **Singleton Pattern**: Uma instância global do cache
- **Thread-Safe**: Operações protegidas com locks
- **Auto-Cleanup**: Remoção automática de documentos expirados
- **Memory Tracking**: Monitoramento de uso de memória
- **LRU Eviction**: Remoção dos documentos menos recentemente acessados

## Validações e Segurança

### Upload
- **Tamanho máximo**: Configurável via FastAPI
- **Tipos permitidos**: `.txt`, `.pdf`
- **Sanitização**: Nomes de arquivo sanitizados
- **UUID seguro**: Chaves imprevisíveis

### Inferência
- **Validação de percentual**: 0 ≤ sample_percentage ≤ 100
- **Validação de tamanho**: 50 ≤ max_sample_length ≤ 2000
- **Providers suportados**: `ollama`, `openai`, `gemini`
- **Timeout**: Configurável por provider

## Monitoramento e Logs

### Métricas Disponíveis
- Tempo de processamento de uploads
- Tamanho de documentos processados
- Taxa de cache hit/miss
- Uso de memória
- Documentos expirados automaticamente

### Logs Estruturados
```python
logger.info(f"Document uploaded: {filename}, size: {file_size_bytes}B, "
           f"processing_time: {processing_time_ms:.1f}ms")
           
logger.info(f"Schema inference: {model_used}, "
           f"sample: {sample_percentage}% ({sample_size} chars), "
           f"processing_time: {processing_time_ms:.1f}ms")
```

## Casos de Uso

### 1. Upload e Análise Rápida
```bash
# 1. Upload
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/schema/upload" \
  -F "file=@document.pdf")

# 2. Extrair chave
DOC_KEY=$(echo $UPLOAD_RESPONSE | jq -r '.key')

# 3. Análise com 50% do documento
curl -X POST "http://localhost:8000/api/v1/schema/infer" \
  -H "Content-Type: application/json" \
  -d "{\"document_key\": \"$DOC_KEY\", \"sample_percentage\": 50}"
```

### 2. Análise com Modelo Específico
```bash
curl -X POST "http://localhost:8000/api/v1/schema/infer" \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "sample_percentage": 75,
    "llm_provider": "gemini",
    "llm_model": "gemini-1.5-pro"
  }'
```

### 3. Monitoramento do Cache
```bash
# Verificar documentos em cache
curl "http://localhost:8000/api/v1/schema/documents"

# Remover documento específico
curl -X DELETE "http://localhost:8000/api/v1/schema/documents/550e8400-e29b-41d4-a716-446655440000"
```

## Próximas Melhorias

- **Persistência**: Cache persistente com Redis/DB
- **Streaming**: Upload de arquivos grandes com streaming
- **Batch Processing**: Análise em lote de múltiplos documentos
- **Webhooks**: Notificações de processamento assíncrono
- **Rate Limiting**: Controle de taxa por usuário/IP