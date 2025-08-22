# Schema Inference API

## Endpoint
- `POST /api/v1/schema/infer`

## Descrição
Infere um schema de grafo (tipos de entidades e relacionamentos) a partir de uma amostra de texto usando o mesmo motor de IA utilizado internamente durante a ingestão de documentos.

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

### 1. Análise Prévia
```bash
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A empresa Microsoft foi fundada por Bill Gates. Ele desenvolveu o sistema operacional Windows.",
    "max_sample_length": 200
  }'
```

### 2. Prototipagem de Documentos
```bash
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "text": "O paciente João foi diagnosticado com diabetes pelo Dr. Silva no Hospital Central."
  }'
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