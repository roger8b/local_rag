# Consulta (Query)

Endpoint
- `POST /api/v1/query`

Payload (JSON)
- `question`: string com a pergunta do usuário (obrigatória)

Resposta
- `answer`: texto gerado
- `sources`: lista de trechos (texto e score) usados na resposta
- `question`: eco da pergunta

Notas
- A recuperação usa busca vetorial sobre nós `:Chunk` no Neo4j
- A geração usa sistema flexível de provedores LLM (configurável via `LLM_PROVIDER`)

Fluxo (Mermaid)
```mermaid
sequenceDiagram
  participant U as Cliente
  participant API as API /query
  participant R as VectorRetriever
  participant G as ResponseGenerator
  participant P as LLMProvider
  participant N as Neo4j
  U->>API: POST /api/v1/query {question}
  API->>R: retrieve(question)
  R->>N: busca vetorial em :Chunk
  N-->>R: chunks relevantes
  R-->>API: fontes (DocumentSource[])
  API->>G: generate_response(question, sources)
  G->>P: delegate via factory pattern
  P-->>G: response
  G-->>API: answer
  API-->>U: 200 OK {answer, sources}
```
