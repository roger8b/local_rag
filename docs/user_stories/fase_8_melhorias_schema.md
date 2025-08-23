# História 8: Melhorias na API de Inferência de Schema

## Contexto
Após a implementação bem-sucedida do sistema de upload de documentos para inferência de schema (História 7), identificamos oportunidades de melhorar a experiência do usuário com maior controle sobre o processamento.

## História de Usuário
**Como** desenvolvedor utilizando a API de inferência de schema  
**Eu quero** poder selecionar o modelo LLM, ver informações detalhadas do documento carregado e controlar o processamento via percentual  
**Para que** eu tenha maior flexibilidade e controle sobre a análise dos meus documentos.

## Requisitos Funcionais

### RF1: Seleção de Modelo no Upload
- Permitir especificar o provider LLM (`ollama`, `openai`, `gemini`) no upload
- Permitir especificar o modelo específico dentro do provider
- Manter compatibilidade com configuração padrão quando não especificado

### RF2: Informações Detalhadas do Documento
- Retornar estatísticas completas do documento após upload:
  - Tamanho do arquivo original (bytes)
  - Tamanho do texto extraído (caracteres)
  - Número de palavras
  - Número de linhas
  - Tempo de processamento do upload

### RF3: Controle por Percentual
- Modificar `max_sample_length` para aceitar percentual (0-100)
- Calcular o tamanho da amostra baseado no percentual do texto total
- Manter backward compatibility com valores absolutos (> 100 = caracteres)

### RF4: Persistência das Configurações
- Armazenar as configurações de modelo junto com o documento no cache
- Usar as configurações armazenadas na inferência (ou permitir override)

## Critérios de Aceitação

### AC1: Upload com Seleção de Modelo
- POST `/api/v1/schema/upload` aceita parâmetros opcionais:
  - `llm_provider`: string ("ollama", "openai", "gemini")
  - `llm_model`: string (modelo específico)
- Configurações são validadas e armazenadas com o documento
- Fallback para configurações padrão quando não especificado

### AC2: Resposta Detalhada do Upload
- Response inclui estatísticas completas:
```json
{
  "key": "uuid",
  "filename": "documento.pdf",
  "file_size_bytes": 1048576,
  "text_stats": {
    "total_chars": 15847,
    "total_words": 2341,
    "total_lines": 156
  },
  "processing_time_ms": 234.5,
  "llm_config": {
    "provider": "ollama",
    "model": "qwen3:8b"
  },
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-15T11:00:00Z"
}
```

### AC3: Controle por Percentual
- `max_sample_length` aceita valores 0-100 (percentual) ou > 100 (caracteres absolutos)
- Exemplos:
  - `50` = 50% do texto total
  - `25` = 25% do texto total  
  - `1500` = 1500 caracteres absolutos (backward compatibility)
- Validação: 0 ≤ percentual ≤ 100, caracteres ≥ 50

### AC4: Inferência com Configurações Persistidas
- Usar configurações de modelo armazenadas no documento por padrão
- Permitir override via parâmetros na requisição de inferência
- Mostrar na resposta qual configuração foi utilizada

### AC5: Endpoint de Informações do Documento
- GET `/api/v1/schema/documents/{key}/info` retorna detalhes completos
- Inclui estatísticas de uso e configurações

## Especificações Técnicas

### Modelos Pydantic Atualizados

```python
class TextStats(BaseModel):
    total_chars: int
    total_words: int  
    total_lines: int

class LLMConfig(BaseModel):
    provider: str
    model: str

class SchemaUploadRequest(BaseModel):
    llm_provider: Optional[str] = Field(None, description="LLM provider (ollama, openai, gemini)")
    llm_model: Optional[str] = Field(None, description="Specific model name")

class SchemaUploadResponse(BaseModel):
    # ... campos existentes ...
    file_size_bytes: int
    text_stats: TextStats
    processing_time_ms: float
    llm_config: LLMConfig

class SchemaInferByKeyRequest(BaseModel):
    # ... campos existentes ...
    sample_percentage: Optional[int] = Field(50, ge=0, le=100, description="Percentage of text to analyze (0-100)")
    # Manter max_sample_length para backward compatibility
```

### DocumentCacheService Enhancements

```python
class CachedDocument:
    # ... campos existentes ...
    file_size_bytes: int
    text_stats: TextStats
    llm_config: LLMConfig
    processing_time_ms: float
```

## Casos de Uso

### Caso 1: Upload com Modelo Específico
```bash
curl -X POST http://localhost:8000/api/v1/schema/upload \
  -F "file=@documento.pdf" \
  -F "llm_provider=openai" \
  -F "llm_model=gpt-4o-mini"
```

### Caso 2: Inferência com Percentual
```bash
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "uuid",
    "sample_percentage": 30
  }'
```

### Caso 3: Override de Modelo na Inferência
```bash
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "document_key": "uuid", 
    "sample_percentage": 75,
    "llm_provider": "gemini",
    "llm_model": "gemini-1.5-pro"
  }'
```

## Benefícios

1. **Flexibilidade**: Escolha do modelo mais adequado para cada documento
2. **Transparência**: Informações detalhadas sobre o processamento
3. **Controle Preciso**: Percentual facilita ajuste proporcional ao tamanho
4. **Experiência Melhorada**: Feedback rico sobre o documento carregado
5. **Backward Compatibility**: Não quebra APIs existentes

## Estimativa
- **Desenvolvimento**: 4-6 horas
- **Testes**: 2-3 horas  
- **Documentação**: 1 hora
- **Total**: 7-10 horas

## Dependências
- História 7 (Upload de Documento) concluída
- Sistema de providers LLM existente
- DocumentCacheService implementado

## Critérios de Pronto
- [ ] Todos os ACs implementados e testados
- [ ] Backward compatibility preservada
- [ ] Documentação atualizada
- [ ] Testes de integração passando
- [ ] Performance não degradada