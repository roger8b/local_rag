# Schema Inference API

## Endpoints
- `POST /api/v1/schema/upload` - Upload de documento para cache temporário
- `POST /api/v1/schema/infer` - Inferência de schema via texto ou chave de documento
- `GET /api/v1/schema/documents` - Listar documentos em cache
- `DELETE /api/v1/schema/documents/{key}` - Remover documento do cache

## Descrição
Sistema completo para inferência de schema de grafo que permite upload seguro de documentos e análise via chaves temporárias, eliminando a necessidade de enviar texto sensível nas requisições.

### Workflow Recomendado
1. **Upload do Documento**: Use `POST /api/v1/schema/upload` para fazer upload do arquivo (.txt ou .pdf)
2. **Obter Chave e Estatísticas**: O sistema retorna uma chave única, estatísticas detalhadas do texto e tempo de processamento
3. **Inferir Schema**: Use `POST /api/v1/schema/infer` com a chave do documento, escolha do modelo LLM e controle por percentual
4. **Gerenciar Cache**: Opcionalmente, liste (`GET /api/v1/schema/documents`) ou remova (`DELETE /api/v1/schema/documents/{key}`) documentos

### Novas Funcionalidades (História 8)

#### 📊 Estatísticas Detalhadas do Documento
Após upload, o sistema retorna informações completas:
- **Tamanho do arquivo**: bytes originais
- **Estatísticas de texto**: caracteres, palavras e linhas  
- **Tempo de processamento**: milissegundos para extração
- **Tipo de arquivo**: detecção automática (.txt/.pdf)

#### 🎯 Controle por Percentual
Nova forma intuitiva de especificar quanto texto analisar:
- **`sample_percentage`**: 0-100% do texto total (padrão: 50%)
- **`max_sample_length`**: caracteres absolutos (preserva compatibilidade)
- **Lógica inteligente**: percentual pequeno garante mínimo de 50 caracteres

#### 🤖 Seleção de Modelo LLM
Escolha o modelo ideal para cada análise:
- **`llm_provider`**: "ollama", "openai" ou "gemini"
- **`llm_model`**: modelo específico dentro do provider
- **Flexibilidade total**: diferentes modelos para diferentes tipos de documento

## Payload (JSON)
```json
{
  "text": "João Silva trabalha na empresa TechCorp desde 2020. Ele desenvolve aplicações web usando React e Node.js.",
  "max_sample_length": 1000
}
```

### Parâmetros
- `text`: string com o texto para análise (obrigatório, mínimo 1 caractere)
- `max_sample_length`: integer com tamanho máximo do texto a analisar (opcional, padrão: 500, range: 50-2000)

## Resposta
```json
{
  "node_labels": ["Person", "Company", "Technology"],
  "relationship_types": ["WORKS_AT", "DEVELOPS_WITH", "USES_TECHNOLOGY"],
  "source": "llm",
  "model_used": "qwen3:8b",
  "processing_time_ms": 1250.5,
  "reason": null
}
```

### Campos da Resposta
- `node_labels`: array de strings com tipos de entidades identificadas
- `relationship_types`: array de strings com tipos de relacionamentos identificados
- `source`: `"llm"` ou `"fallback"` (indica se foi gerado por IA ou schema padrão)
- `model_used`: string com nome do modelo LLM usado (null se fallback)
- `processing_time_ms`: float com tempo de processamento em milissegundos
- `reason`: string com motivo do fallback (null se sucesso com LLM)

## Cenários de Uso

### 1. Upload e Análise Segura (Recomendado)
```bash
# 1. Upload do documento - agora retorna estatísticas detalhadas
curl -X POST http://localhost:8000/api/v1/schema/upload \
  -F "file=@documento.pdf"

# Resposta enriquecida:
{
  "key": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documento.pdf",
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

# 2. Inferir schema com controle percentual e seleção de modelo
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "sample_percentage": 75,
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini"
  }'
```

### 2. Análise Direta (Backward Compatibility)
```bash
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A empresa Microsoft foi fundada por Bill Gates. Ele desenvolveu o sistema operacional Windows.",
    "max_sample_length": 200
  }'
```

### 3. Novos Controles de Análise
```bash
# Análise de apenas 25% do documento (ideal para documentos grandes)
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "sample_percentage": 25
  }'

# Análise com modelo específico para documentos técnicos
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "sample_percentage": 100,
    "llm_provider": "gemini",
    "llm_model": "gemini-1.5-pro"
  }'

# Backward compatibility - ainda funciona como antes
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "550e8400-e29b-41d4-a716-446655440000",
    "max_sample_length": 1000
  }'
```

### 4. Gerenciamento de Cache com Informações Detalhadas
```bash
# Listar documentos em cache - agora com estatísticas completas
curl -X GET http://localhost:8000/api/v1/schema/documents

# Resposta enriquecida:
{
  "documents": [
    {
      "key": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "documento.pdf",
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

# Remover documento específico
curl -X DELETE http://localhost:8000/api/v1/schema/documents/550e8400-e29b-41d4-a716-446655440000
```

## Comportamento

### LLM Disponível
- Usa o modelo configurado em `LLM_MODEL` (padrão: qwen3:8b)
- Analisa o texto e infere schema personalizado
- Retorna `source: "llm"` com detalhes do modelo

### LLM Indisponível (Fallback)
- Retorna schema genérico padrão:
  - `node_labels`: ["Entity", "Concept"]
  - `relationship_types`: ["RELATED_TO", "MENTIONS"]
- Retorna `source: "fallback"` com motivo na propriedade `reason`

### Tratamento de Erros
- **422**: Validação (texto vazio, parâmetros inválidos)
- **500**: Erro interno (sempre retorna schema fallback)

## Limitações
- Texto truncado automaticamente se exceder `max_sample_length`
- Análise limitada pela capacidade do modelo LLM configurado
- Tempo de processamento varia com tamanho do texto e disponibilidade do LLM

## Integração
Este endpoint usa a mesma lógica da função `_infer_graph_schema()` do `IngestionService`, garantindo consistência com o processo de ingestão de documentos.

## Exemplo Prático

### Input
```json
{
  "text": "O desenvolvedor Pedro trabalha na startup TechFlow. Ele usa Python para criar APIs REST que conectam com bancos de dados PostgreSQL.",
  "max_sample_length": 500
}
```

### Output
```json
{
  "node_labels": [
    "Person",
    "Company", 
    "ProgrammingLanguage",
    "Technology",
    "Database"
  ],
  "relationship_types": [
    "WORKS_AT",
    "USES",
    "CREATES",
    "CONNECTS_TO"
  ],
  "source": "llm",
  "model_used": "qwen3:8b",
  "processing_time_ms": 1847.3,
  "reason": null
}
```

Este schema sugere que o sistema criará nós para pessoas, empresas, linguagens de programação, tecnologias e bancos de dados, conectados por relacionamentos como "trabalha em", "usa", "cria" e "conecta com".