# Histórias de Usuário - Local RAG System

Este diretório contém todas as histórias de usuário implementadas no sistema Local RAG, organizadas por fase de desenvolvimento.

## Índice das Histórias

### Fase 1: Fundação do Sistema RAG
- **[História 1](./fase_1.md)**: Implementação básica do sistema RAG com Ollama e Neo4j
  - Retrieval baseado em vetores
  - Geração de respostas com LLM
  - Interface web com Streamlit

### Fase 2: Suporte Multi-Provider
- **[História 2](./fase_2.md)**: Arquitetura flexível de providers LLM
  - Factory pattern para providers
  - Interface base padronizada

### Fase 3: Provider Google Gemini  
- **[História 3](./fase_3.md)**: Integração com Google Gemini
  - Support completo à API Gemini
  - Configuração via environment

### Fase 4: Provider OpenAI
- **[História 4](./fase_4.md)**: Integração com OpenAI
  - GPT models para geração e embeddings
  - Múltiplas sub-histórias de refinamento ([4.1](./fase_4_1.md), [4.2](./fase_4_2.md), [4.3](./fase_4_3.md), [4.4](./fase_4_4.md))

### Fase 5: Seleção Dinâmica de Provider
- **[História 5](./fase_5.md)**: Interface de seleção dinâmica
  - Streamlit sidebar para provider selection
  - Sub-histórias para melhorias ([5.1](./fase_5_1.md), [5.2](./fase_5_2.md), [5.3](./fase_5_3.md))

### Fase 6: API de Schema Inference
- **[História 6](./fase_6.md) / [Schema API](./fase_6_schema_api.md)**: Inferência de schema de grafos
  - Análise automática de documentos
  - Sugestão de node labels e relationships

### Fase 7: Sistema de Upload Seguro
- **[História 7](./fase_7_schema_upload.md)**: Upload e cache de documentos
  - Upload multipart com validação
  - Sistema de cache em memória com TTL
  - Chaves UUID para segurança
  - 4 endpoints completos (upload, infer, list, remove)

### Fase 8: Melhorias na API de Schema
- **[História 8](./fase_8_melhorias_schema.md)**: Controle avançado e estatísticas
  - Seleção de modelo LLM no endpoint de inferência
  - Estatísticas detalhadas dos documentos
  - Controle por percentual (0-100%) para amostragem
  - Informações completas de processamento

## Status de Implementação

| História | Status | Testes | Documentação |
|----------|--------|--------|-------------|
| História 1 | ✅ Completa | ✅ 10 testes | ✅ Documentada |
| História 2 | ✅ Completa | ✅ Integrado | ✅ Documentada |
| História 3 | ✅ Completa | ✅ Integrado | ✅ Documentada |
| História 4 | ✅ Completa | ✅ Integrado | ✅ Documentada |
| História 5 | ✅ Completa | ✅ Integrado | ✅ Documentada |
| História 6 | ✅ Completa | ✅ 10 testes | ✅ Documentada |
| História 7 | ✅ Completa | ✅ 16 testes | ✅ Documentada |
| História 8 | ✅ Completa | ✅ 8 testes | ✅ Documentada |

## Cobertura de Testes

- **Total de Testes**: 41 testes passando
  - Schema API: 34 testes (10 originais + 16 upload + 8 melhorias)
  - Retriever: 7 testes
- **Cobertura**: 100% dos endpoints principais
- **Metodologia**: Test-Driven Development (TDD)

## Arquivos de Suporte

- **[Melhorias de Testes](./historia_melhoria_testes.md)**: História para correção de warnings em testes

## Próximas Histórias

As próximas histórias planejadas incluem:
- Métricas e monitoring
- Cache persistente
- Otimizações de performance
- Interface web aprimorada