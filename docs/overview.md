# Visão Geral e Arquitetura

Este projeto implementa um sistema de Retrieval-Augmented Generation (RAG) local usando Python, LangChain e Neo4j como banco de dados vetorial e de grafos. O sistema permite ingestão, indexação e recuperação de documentos para gerar respostas contextualizadas usando múltiplos provedores de modelos de linguagem (Ollama, OpenAI, Google Gemini).

Arquitetura (alto nível)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Documentos    │    │   Processamento │    │   Armazenamento │
│                 │    │                 │    │                 │
│ • TXTs          │───▶│ • Splitter      │───▶│ • Neo4j         │
│ • PDFs          │    │ • Embeddings    │    │ • Vetores       │
│ • Webpages      │    │ • Metadados     │    │ • Relacionamentos│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐           │
│   Interface     │    │   Geração       │           │
│                 │    │                 │           │
│ • API REST      │◀───│ • Multi-LLM     │◀──────────┘
│ • Streamlit UI  │    │ • Prompt Eng.   │
└─────────────────┘    └─────────────────┘
```

Componentes principais
- Ingestão: carregamento, chunking e metadados
- Embeddings: Ollama (padrão) e OpenAI (opcional)
- Armazenamento: nós `:Chunk` com `embedding` e relacionamentos
- Recuperação: busca vetorial + grafo
- Geração: Sistema flexível com múltiplos provedores LLM (Ollama, OpenAI, Gemini)

Casos de uso
- Base de conhecimento; documentação técnica; FAQ inteligente; análise de documentos; pesquisa acadêmica
