# História 6: API para Inferência de Schema de Grafo

## 🎯 Objetivo
Criar uma API REST que permita aos usuários inferir um schema de grafo (entidades e relacionamentos) com base em uma amostra de texto, utilizando a funcionalidade existente `_infer_graph_schema`.

## 📋 Contexto
O sistema RAG já possui uma funcionalidade interna que analisa documentos e infere automaticamente um schema de grafo apropriado (tipos de entidades e relacionamentos). Esta funcionalidade está encapsulada na função `_infer_graph_schema` do `IngestionService`, mas não está exposta via API para uso externo.

## 🎯 Casos de Uso
1. **Análise Prévia**: Desenvolvedores podem analisar um texto antes da ingestão para entender que tipo de schema será gerado
2. **Prototipagem**: Equipes podem experimentar com diferentes tipos de documentos para entender a estrutura de dados resultante
3. **Documentação**: Gerar automaticamente documentação sobre a estrutura de dados esperada
4. **Validação**: Verificar se o conteúdo gerará um schema útil antes do processamento completo

## 📝 História do Usuário
**Como** desenvolvedor integrador do sistema RAG  
**Eu quero** poder enviar uma amostra de texto para uma API  
**Para que** eu possa obter uma previsão do schema de grafo que será gerado (tipos de entidades e relacionamentos)  
**Sem** precisar fazer a ingestão completa do documento

## ✅ Critérios de Aceitação

### AC1: Endpoint de Inferência de Schema
- **Dado** que existe um endpoint `POST /api/v1/schema/infer`
- **Quando** envio uma requisição com uma amostra de texto
- **Então** recebo um schema inferido com node_labels e relationship_types
- **E** a resposta deve ter status 200

### AC2: Validação de Entrada
- **Dado** que envio uma requisição sem texto ou com texto vazio
- **Quando** chamo o endpoint
- **Então** recebo status 422 com mensagem de erro apropriada

### AC3: Fallback para Ollama Indisponível
- **Dado** que o Ollama não está disponível
- **Quando** chamo o endpoint
- **Então** recebo um schema padrão/fallback
- **E** o status deve ser 200 com uma indicação de que foi usado fallback

### AC4: Resposta Estruturada
- **Dado** que a inferência foi bem-sucedida
- **Quando** recebo a resposta
- **Então** ela deve conter:
  - `node_labels`: array de strings com tipos de entidades
  - `relationship_types`: array de strings com tipos de relacionamentos
  - `source`: indicação se foi "llm" ou "fallback"
  - `model_used`: modelo LLM utilizado (se aplicável)

### AC5: Documentação OpenAPI
- **Dado** que acesso a documentação da API
- **Quando** visualizo o endpoint `/schema/infer`
- **Então** vejo exemplos claros de request/response
- **E** documentação dos parâmetros e possíveis códigos de status

### AC6: Compatibilidade
- **Dado** que a API é implementada
- **Quando** testo as APIs existentes
- **Então** nenhuma funcionalidade existente deve ser afetada
- **E** os testes existentes devem continuar passando

## 🔧 Especificação Técnica

### Request
```json
POST /api/v1/schema/infer
Content-Type: application/json

{
  "text": "João Silva trabalha na empresa TechCorp desde 2020. Ele é responsável pelo desenvolvimento de aplicações web utilizando React e Node.js. A TechCorp é uma startup de tecnologia focada em soluções de e-commerce.",
  "max_sample_length": 1000  // opcional, default 500
}
```

### Response Success (200)
```json
{
  "node_labels": [
    "Person",
    "Company", 
    "Technology",
    "Role",
    "Industry"
  ],
  "relationship_types": [
    "WORKS_AT",
    "RESPONSIBLE_FOR", 
    "USES",
    "FOUNDED_IN",
    "FOCUSES_ON"
  ],
  "source": "llm",
  "model_used": "qwen3:8b",
  "processing_time_ms": 1250
}
```

### Response Fallback (200)
```json
{
  "node_labels": [
    "Entity",
    "Concept"
  ],
  "relationship_types": [
    "RELATED_TO",
    "MENTIONS"
  ],
  "source": "fallback",
  "model_used": null,
  "processing_time_ms": 15,
  "reason": "Ollama service unavailable"
}
```

### Response Error (422)
```json
{
  "detail": "Text field is required and cannot be empty"
}
```

## 🧪 Plano de Testes

### Testes Unitários
1. **Test de Validação de Entrada**
   - Texto vazio/nulo → 422
   - Texto muito longo → processamento com truncagem
   - Parâmetros opcionais funcionando

2. **Test de Schema Inference**
   - Mock do Ollama retornando schema válido
   - Validação da estrutura de resposta
   - Verificação de tipos de dados

3. **Test de Fallback**
   - Mock do Ollama indisponível
   - Retorno do schema padrão
   - Indicação correta da fonte

### Testes de Integração
1. **Test End-to-End**
   - Requisição real com texto de exemplo
   - Verificação de tempo de resposta
   - Validação da estrutura JSON

2. **Test de Compatibilidade**
   - APIs existentes não afetadas
   - Sem regressões nos endpoints atuais

## 🚀 Implementação

### Arquivos a Criar/Modificar
1. **`src/models/api_models.py`**: Adicionar models para request/response
2. **`src/api/routes.py`**: Adicionar novo endpoint
3. **`tests/integration/test_schema_api.py`**: Testes de integração
4. **`tests/unit/test_schema_inference.py`**: Testes unitários

### Dependências
- Reutilizar `IngestionService._infer_graph_schema()`
- Manter compatibilidade com settings atuais
- Seguir padrões de erro handling existentes

## 📊 Definição de Pronto (DoD)
- [ ] Endpoint implementado e funcionando
- [ ] Modelos Pydantic criados
- [ ] Documentação OpenAPI gerada
- [ ] Testes unitários com cobertura > 90%
- [ ] Testes de integração passando
- [ ] Nenhuma regressão nos testes existentes
- [ ] Tratamento de erros robusto
- [ ] Logging adequado implementado
- [ ] Code review aprovado

## 🔄 Metodologia
- **TDD**: Implementar testes primeiro
- **Incremental**: Desenvolver em pequenos commits
- **Não-disruptivo**: Zero impacto nas APIs existentes
- **Documentação**: Atualizar README com novo endpoint

## 💡 Benefícios Esperados
1. **Transparência**: Usuários podem ver que schema será gerado
2. **Debugging**: Facilita troubleshooting de problemas de ingestão  
3. **Integração**: Permite integrações mais robustas com sistemas externos
4. **Performance**: Evita ingestão completa apenas para ver o schema
5. **UX**: Melhora experiência do desenvolvedor

## 🎯 Exemplo de Uso
```bash
# Testar schema para documento técnico
curl -X POST http://localhost:8000/api/v1/schema/infer \
  -H "Content-Type: application/json" \
  -d '{
    "text": "O framework FastAPI utiliza Pydantic para validação. SQLAlchemy é usado para ORM. Redis serve como cache."
  }'
```

**Resposta esperada:**
```json
{
  "node_labels": ["Framework", "Library", "Technology", "Purpose"],
  "relationship_types": ["USES", "SERVES_AS", "PROVIDES"],
  "source": "llm",
  "model_used": "qwen3:8b"
}
```