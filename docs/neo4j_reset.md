# Limpeza/Reset do Neo4j

Script utilitário: `scripts/clear_database.py`

O que faz
- `DROP INDEX document_embeddings IF EXISTS`
- `MATCH (n:Chunk) DETACH DELETE n`
- Mensagens de status e fechamento do driver

Como usar
```
python scripts/clear_database.py
# Confirme com 'yes' ou 'sim'
```

Após a limpeza
- Nova ingestão recria automaticamente o índice vetorial `document_embeddings`
- A dimensão do índice reflete `OPENAI_EMBEDDING_DIMENSIONS` (default 768)
