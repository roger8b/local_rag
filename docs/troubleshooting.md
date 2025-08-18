# Troubleshooting

Erros comuns
- 500 ao ingerir com OpenAI: verifique `OPENAI_API_KEY` ou use `embedding_provider=ollama`
- Neo4j indisponível: defina `NEO4J_VERIFY_CONNECTIVITY=false` para não falhar no startup e rode a ingestão em modo degradado
- Ollama não responde: confirme `OLLAMA_BASE_URL` e que os modelos foram baixados (`ollama pull nomic-embed-text`)

Dicas
- Veja logs da API para mensagens de erro detalhadas
- Após limpar o banco, a primeira ingestão recria o índice vetorial
- Em desenvolvimento, o serviço usa vetores zero como fallback se embeddings falharem, evitando 500
