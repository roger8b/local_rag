# Local RAG System - Multi-Provider Architecture

[![CI](https://github.com/roger8b/local_rag/actions/workflows/tests.yml/badge.svg)](https://github.com/roger8b/local_rag/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/roger8b/local_rag/branch/main/graph/badge.svg)](https://codecov.io/gh/roger8b/local_rag)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-red.svg)](https://neo4j.com/)

## 🎯 Visão Geral

Sistema de **Retrieval-Augmented Generation (RAG)** local com suporte a múltiplos providers LLM, inferência de schema de grafos e gerenciamento avançado de documentos. Desenvolvido com arquitetura flexível usando padrões Strategy e Factory.

### ✨ Funcionalidades Principais

- 🤖 **Multi-Provider LLM**: Ollama, OpenAI, Google Gemini
- 📊 **Schema Inference**: Análise automática para estruturas de grafos
- 📁 **Document Management**: Upload seguro com cache e TTL
- 🔍 **Vector Retrieval**: Busca semântica com Neo4j
- 🎛️ **Dynamic Selection**: Seleção de provider e modelo em runtime
- 📈 **Detailed Analytics**: Estatísticas completas de documentos e processamento
- 🔒 **Secure Uploads**: Sistema de chaves UUID com expiração automática

## 📚 Documentação

### Documentação Principal
- 📖 [Visão Geral](docs/overview.md) - Introdução e conceitos
- 🏗️ [Arquitetura](docs/architecture.md) - Estrutura e padrões do sistema
- ⚙️ [Setup & Configuração](docs/setup.md) - Instalação e execução
- 🔧 [Configuração Avançada](docs/configuration.md) - Variáveis e flags
- 📥 [Ingestão](docs/ingestion.md) - Upload e processamento
- 🔍 [Query API](docs/query.md) - Consultas e retrieval
- 🗂️ [Schema Inference](docs/schema_inference.md) - Inferência de grafos
- 🔧 [Troubleshooting](docs/troubleshooting.md) - Solução de problemas

### Histórias de Usuário
- 📋 [User Stories](docs/user_stories/README.md) - 8 histórias implementadas
- 🚀 [Implementation Phases](docs/implementation_phases/) - Fases de desenvolvimento

## ⚡ Quick Start

### 1. Configuração do Ambiente
```bash
# Clone o repositório
git clone https://github.com/roger8b/local_rag.git
cd local_rag

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações
```

### 2. Instalação e Execução
```bash
# Instale as dependências
pip install -r requirements.txt

# Inicie a API
python run_api.py

# OU inicie o Streamlit (interface web)
streamlit run streamlit_app.py
```

### 3. Principais Endpoints da API

Acesse http://localhost:8000/docs para documentação interativa:

#### 📊 Schema Inference (Histórias 6-8)
- `POST /api/v1/schema/upload` - Upload com estatísticas detalhadas
- `POST /api/v1/schema/infer` - Inferência com controle percentual e seleção de modelo
- `GET /api/v1/schema/documents` - Listar cache com informações completas
- `DELETE /api/v1/schema/documents/{key}` - Remover do cache

#### 📚 Document Management
- `POST /api/v1/ingest` - Upload de documentos (.txt, .pdf)
- `POST /api/v1/query` - Consultas RAG
- `GET /api/v1/models/{provider}` - Listar modelos disponíveis
- `GET /api/v1/documents` - Listar documentos processados
- `DELETE /api/v1/documents/{doc_id}` - Remover documento

## 🔧 Configuração

### Variáveis de Ambiente Principais
```bash
# Providers LLM
LLM_PROVIDER=ollama          # ollama, openai, gemini
EMBEDDING_PROVIDER=ollama    # ollama, openai

# API Keys (apenas para providers externos)
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Neo4j (opcional)
NEO4J_VERIFY_CONNECTIVITY=false  # Para ambientes sem Neo4j
```

### Interface Web (Streamlit)
- 💬 **Chat Interface**: Consultas RAG interativas
- 📤 **Document Upload**: Upload e gerenciamento
- 🎛️ **Provider Selection**: Seleção dinâmica de LLM
- 📊 **Document Manager**: Visualização e remoção (`pages/03_document_manager.py`)

## 🧪 Testes

- **Total**: 41 testes automatizados
- **Cobertura**: 100% dos endpoints principais
- **Metodologia**: Test-Driven Development (TDD)

```bash
# Executar todos os testes
pytest

# Executar testes específicos
pytest tests/integration/test_schema_improvements.py -v
```

## 🏗️ Arquitetura

- **Padrões**: Strategy, Factory, Dependency Injection
- **Providers**: Arquitetura plugável para LLMs
- **Cache**: Sistema em memória com TTL
- **API**: FastAPI com documentação automática
- **Database**: Neo4j para vectors e grafos
