# Instalação e Execução

Pré-requisitos
- Python 3.9+
- Neo4j 5.x (com APOC recomendado)
- Ollama para modelos locais (opcional)

Criar ambiente e instalar dependências
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

Configurar variáveis de ambiente
```
cp .env.example .env
# Edite .env conforme seu ambiente (Neo4j, OpenAI, Ollama)
```

Subir API
```
python run_api.py
# ou
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Acessar documentação interativa
- http://localhost:8000/docs
