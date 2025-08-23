## Refinamento Colaborativo: Histórias da Fase 2: A Ingestão Dinâmica via API

---
### História 1: Endpoint de API para Ingestão de Documentos
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero enviar um arquivo de texto (`.txt`) para um endpoint da API (`POST /ingest`), para que ele seja processado e adicionado à base de conhecimento de forma programática.
* **Requisitos / Detalhes:**
    * Deve ser criado um endpoint `POST /ingest`.
    * O endpoint deve ser capaz de receber uploads de arquivos (`multipart/form-data`).
    * O sistema deve validar se o arquivo enviado é do tipo `.txt`.
    * Ao receber um arquivo válido, o sistema deve executar o pipeline completo de ingestão: carregar, dividir em chunks, gerar embeddings e persistir no Neo4j.
    * Em caso de sucesso, a API deve retornar uma resposta confirmando que o processamento foi iniciado ou concluído.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a API está em execução, quando eu envio uma requisição `POST` para `/ingest` com um arquivo `.txt` válido, então eu recebo uma resposta de sucesso (e.g., `201 Created`) e os dados do arquivo são persistidos no Neo4j.
    * **AC 2:** Dado que a API está em execução, quando eu envio um arquivo com uma extensão não suportada (e.g., `.pdf` ou `.jpg`) para `/ingest`, então eu recebo uma resposta de erro (`415 Unsupported Media Type`).
    * **AC 3:** Dado que um novo documento foi ingerido com sucesso via API, quando eu faço uma consulta na API `/query` sobre o conteúdo daquele documento, então eu recebo uma resposta relevante.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de integração para o endpoint `/ingest` foram criados e estão passando.
    * [ ] A funcionalidade foi validada de ponta a ponta (upload via API, confirmação via consulta).
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Refatorar a lógica do script de ingestão da Fase 1 para um serviço reutilizável dentro da aplicação. Criar um novo endpoint no FastAPI que lida com o upload de arquivos e chama este serviço.
* **Backend:**
    * - **Refatoração:** Migrar a lógica de `scripts/ingest_documents.py` para um novo módulo de serviço, como `src/application/services/ingestion_service.py`. Este serviço irá conter as etapas de chunking, embedding e armazenamento.
    * - **API:** Criar um novo endpoint `POST /api/v1/ingest` no FastAPI.
    * - **Dependência:** Adicionar `python-multipart` ao `requirements.txt` para que o FastAPI possa lidar com uploads de formulários.
    * - **Lógica do Endpoint:** Utilizar `UploadFile` do FastAPI para receber o arquivo. O endpoint irá realizar a validação do tipo de arquivo e, em seguida, passar o conteúdo do arquivo para o `ingestion_service`.
    * - **Resposta:** Em caso de sucesso, retornar um JSON como `{"status": "success", "filename": "nome_do_arquivo.txt"}`.
* **Frontend:**
    * - Nenhuma implementação de frontend nesta fase.
* **Banco de Dados:**
    * - Nenhuma alteração de schema. O serviço de ingestão utilizará as mesmas consultas Cypher da Fase 1 para criar nós `:Chunk` e o índice vetorial.
* **Questões em Aberto / Riscos:**
    * - **Processamento Síncrono:** A ingestão de um documento grande irá bloquear a requisição HTTP, o que pode causar timeouts. Para esta fase, uma abordagem síncrona é aceitável, mas devemos considerar migrar para tarefas em segundo plano (background tasks) em fases futuras para melhorar a responsividade da API.
    * - **Segurança:** O endpoint estará aberto para qualquer um fazer upload. Futuramente, precisaremos adicionar autenticação. Risco baixo para o ambiente de desenvolvimento inicial.

---
### História 2: Cliente CLI para Upload de Documentos
* **Tipo:** Funcional / Ferramenta

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero uma ferramenta de linha de comando para enviar um arquivo `.txt` local para o endpoint de ingestão, para que eu possa adicionar novos documentos ao sistema de forma rápida e fácil a partir do meu terminal.
* **Requisitos / Detalhes:**
    * Deve ser criado um script Python em `scripts/run_ingest.py`.
    * O script deve aceitar um argumento de linha de comando (`--file`) para especificar o caminho do arquivo a ser enviado.
    * A ferramenta deve construir e enviar uma requisição `POST multipart/form-data` para o endpoint `/ingest` da API.
    * O resultado da operação (sucesso ou erro retornado pela API) deve ser impresso no console.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a API está rodando, quando eu executo o comando `python scripts/run_ingest.py --file /path/to/my_doc.txt`, então o arquivo é enviado para a API e a resposta JSON do servidor é impressa no meu terminal.
    * **AC 2:** Dado que eu forneço um caminho para um arquivo que não existe, quando eu executo o script, então ele exibe uma mensagem de erro "Arquivo não encontrado" e não tenta fazer a chamada à API.
    * **AC 3:** Dado que a API não está rodando, quando eu executo o script, então ele exibe uma mensagem de erro de conexão.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] O script foi testado com sucesso em um ambiente de desenvolvimento contra a API local.
    * [ ] O script inclui instruções de uso básicas (seja em comentários ou através da flag `--help`).

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Criar um script Python simples que utiliza a biblioteca `requests` para fazer a chamada HTTP e `argparse` para uma interface de linha de comando amigável.
* **Backend (Script Cliente):**
    * - **Arquivo:** Criar `scripts/run_ingest.py`.
    * - **Dependências:** Adicionar a biblioteca `requests` ao `requirements.txt`.
    * - **Argumentos:** Usar `argparse` para definir e ler o argumento `--file`.
    * - **Lógica do Script:**
        * Verificar se o caminho do arquivo fornecido existe no sistema de arquivos local.
        * Definir a URL do endpoint da API (e.g., `http://localhost:8000/api/v1/ingest`). Idealmente, ler de uma variável de ambiente para flexibilidade.
        * Abrir o arquivo em modo de leitura binária (`'rb'`).
        * Usar `requests.post(url, files={'file': file_object})` para enviar a requisição.
        * Imprimir o status da resposta e o corpo JSON de forma legível.
        * Envolver a chamada de rede em um bloco `try...except` para capturar `requests.exceptions.ConnectionError`.
* **Frontend:**
    * - N/A.
* **Banco de Dados:**
    * - N/A (o script não interage diretamente com o banco de dados).
* **Questões em Aberto / Riscos:**
    * - **Configuração da URL:** A URL da API estará inicialmente hardcoded. Seria melhor permitir que seja configurada via variável de ambiente (`API_BASE_URL`) para facilitar o uso em diferentes ambientes (local, staging, etc.).

---