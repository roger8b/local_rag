# História Técnica: Melhoria da Cobertura de Testes e Robustez

## Contexto
O projeto já possui uma suíte ampla de testes (unitários, integração, e2e e UI), porém há lacunas relevantes de cobertura e alguns gargalos de configuração que impedem mensuração consistente. O objetivo desta história é elevar a qualidade e a confiabilidade da base de testes, cobrindo caminhos de erro e fallbacks críticos, e padronizando a infraestrutura de execução e medição de cobertura.

## Diagnóstico Atual
- Ferramentas:
  - `pytest-cov` e `coverage` não estavam ativos no ambiente local (args `--cov` não reconhecidos).
  - Execuções anteriores registradas em `pytest_output.txt` mostram 38 testes coletados, 32 passando e 6 falhas relacionadas a execução assíncrona sem plugin adequado.
- Configuração:
  - `pytest.ini` contém `asyncio_mode = auto`, mas precisamos garantir a presença/ativação de `pytest-asyncio` no ambiente para suportar testes `async def` sem decoradores.
- Heurística de cobertura (estática):
  - Módulos potencialmente sem testes diretos: `src/api/routes.py` e `src/application/services/ingestion_service copy.py` (arquivo duplicado; candidato a exclusão/ignorância na cobertura).
- Áreas com alto risco e baixa cobertura de caminhos de erro:
  - `src/retrieval/retriever.py`: retries, erros HTTP, mismatch de dimensões, fallback textual, modos com Neo4j indisponível, `get_system_status()` e `health_check()`.
  - `src/application/services/ingestion_service.py`: criação de índice, geração de embeddings (OpenAI/Ollama) e fallbacks, inferência de esquema, extração genérica, persistência com APOC indisponível, fluxo degradado.
  - `src/api/routes.py`: validações (arquivo vazio 422), erros do gerador (500), uso de `provider` override.
  - `src/api/client.py`: inclusão condicional de `provider` no payload.
  - `src/ui/pages/query_interface.py`: estados de providers por ENV e mensagens de erro amigáveis.
  - `src/models/api_models.py`: validação de `provider` inválido (422) além de `question` vazio.

## Objetivos (medíveis)
- Cobertura de linha/módulo:
  - `src/retrieval/` ≥ 85%
  - `src/application/services/ingestion_service.py` ≥ 80%
  - `src/api/routes.py` ≥ 80%
  - `src/api/client.py` e `src/ui/pages/query_interface.py` ≥ 85%
- Infra: execução local com `pytest --cov=src --cov-report=term-missing -m "not e2e"` sem falhas de plugin/configuração.

## Escopo
- Adição de testes unitários e de integração leve (com mocks) cobrindo caminhos de sucesso, erro e fallback.
- Ajustes mínimos de configuração de teste/cobertura para mensuração consistente.
- Não inclui reestruturações de código fora do necessário para testabilidade.

## Plano Técnico
1) Infra de Testes
- Garantir instalação dos plugins listados em `requirements.txt` (incluem `pytest`, `pytest-asyncio`, `pytest-cov`).
- Opcional: adicionar `addopts` em `pytest.ini` para padronizar cobertura:
  - `addopts = --cov=src --cov-report=term-missing:skip-covered`
- Marcação: manter `-m "not e2e"` para cobertura (e2e fora do escopo de cobertura).
- Cobertura: Ignorar arquivo duplicado não utilizado `src/application/services/ingestion_service copy.py` via `.coveragerc` (se criado) ou remover o arquivo se confirmado como obsoleto.

2) Casos de Teste por Módulo
- `src/retrieval/retriever.py`
  - `generate_embedding()`
    - Sucesso (200) com `embeddings` válidos.
    - `HTTPStatusError` com retries e falha final.
    - Resposta sem chave `embeddings` → `ValueError`.
    - Mismatch de dimensões vs. armazenado → `ValueError`.
    - Ollama indisponível → exceção clara.
  - `retrieve()`
    - Vetorial retorna vazio → fallback textual retorna resultados.
    - Exceção na vetorial → fallback textual; ambos falham → exceção final.
  - `get_system_status()`
    - Com Neo4j ok: conta de chunks e presença/ausência do índice vetorial.
    - Com Neo4j desabilitado: campos condizentes sem exceção.
  - `health_check()`
    - Ollama saudável vs. não saudável; quando saudável, teste de embedding populando `dimensions`.
- `src/application/services/ingestion_service.py`
  - `_ensure_vector_index()`
    - Índice inexistente → cria; Neo4j indisponível → log e segue.
  - `_generate_embeddings()`
    - OpenAI sem `OPENAI_API_KEY` → `ValueError` (fail-fast).
    - OpenAI com erro HTTP.
    - Ollama com erro HTTP e com payload sem `embeddings`.
    - Contagem de embeddings diferente do número de chunks.
  - `_infer_graph_schema()`
    - Sucesso com JSON válido.
    - HTTP 4xx/5xx e exceções → fallback de esquema padrão.
  - `_call_ollama_for_extraction()`
    - Sucesso com JSON válido.
    - HTTP/erro → `{entities:[], relationships:[]}`.
  - `ingest_from_content()`
    - Falha em `_generate_embeddings` → fallback para vetores zero e retorno com `status` e contagem de chunks.
    - Ollama indisponível → pula extração; fluxo ainda retorna sucesso.
- `src/api/routes.py`
  - `/ingest`
    - Arquivo vazio → 422 (mensagem adequada).
    - Sucesso com `.txt` mockando serviço.
  - `/query`
    - `provider` override definido (ex.: `openai`) refletido em `provider_used`.
    - Exceção no gerador → 500 com `detail`.
- `src/api/client.py`
  - `query()` inclui `provider` no payload quando informado; erros de `requests` retornam `{ok: False, error}`.
- `src/ui/pages/query_interface.py`
  - `get_provider_status()` para `openai`/`gemini` com/sem envs válidas.
  - `render_page()` (via st fake) caminho de erro mostra mensagem amigável e não quebra quando não há `sources`.
- `src/models/api_models.py`
  - Validação de `provider` inválido resulta em 422 no endpoint.

3) Estratégia de Mocks
- `httpx.AsyncClient`: mock de `get`/`post` retornando objetos com `.json()` e `.raise_for_status()` (assíncrono seguro).
- `neo4j.GraphDatabase.driver`: mock do driver/sessão, incluindo consultas usadas (e.g., `SHOW INDEXES`, `MATCH (c:Chunk) RETURN count`).
- `openai`/`google-generativeai`: mocks de clientes/métodos para evitar rede.
- `fastapi.TestClient`: usado para endpoints; patch das dependências internas conforme necessário.

## Critérios de Aceitação
- Execução de `pytest -q -m "not e2e"` com 0 falhas e sem erros de plugin assíncrono.
- Execução de cobertura `pytest --cov=src --cov-report=term-missing -m "not e2e"` produz relatório, sem módulos críticos “não importados”.
- Metas de cobertura por módulo atendidas (ver Objetivos).
- Testes adicionados exercitam pelo menos um caminho de erro/fallback em cada componente listado.

## Riscos e Mitigações
- Dependência de rede/serviços (Ollama, OpenAI, Neo4j): mitigar com mocks/fakes; não rodar testes que exigem rede real.
- Flutuações de API: isolar contratos esperados em helpers de mock e validar somente estrutura essencial.
- Tempo de execução elevado: preferir unitários rápidos; isolar integração leve com mocks.

## Fora de Escopo
- Testes e2e de performance/latência.
- Alterações arquiteturais significativas.
- Execução contra instâncias reais de Neo4j ou LLMs.

## Estimativa
- Implementação de infraestrutura e primeiros testes críticos: 1–2 dias.
- Cobertura completa conforme plano: +1–2 dias (dependendo de revisão e ajustes finos).

## Comandos Úteis
- Instalação (local): `pip install -r requirements.txt`
- Testes rápidos: `pytest -q -m "not e2e"`
- Cobertura: `pytest --cov=src --cov-report=term-missing -m "not e2e"`

---
Atualizar este documento ao fechar a história com os números finais de cobertura por módulo e links dos PRs correspondentes.
