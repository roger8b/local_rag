## Refinamento Colaborativo: Histórias da Fase 1: O Serviço de Respostas (Read-Only)

---
### História 1: Endpoint de Consulta da API para Respostas RAG
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero enviar uma pergunta para um endpoint da API (`POST /query`) e receber uma resposta contextualizada, para que eu possa validar o funcionamento do núcleo do sistema RAG (recuperação e geração).
* **Requisitos / Detalhes:**
    * Deve existir um endpoint `POST /query`.
    * O corpo da requisição deve ser um JSON contendo um campo `question` (string).
    * O sistema deve usar a pergunta para buscar chunks de documentos relevantes no banco de dados vetorial (Neo4j).
    * Os chunks recuperados devem ser usados como contexto para uma chamada a um LLM local (Ollama).
    * A resposta da API deve ser um JSON contendo a resposta gerada pelo LLM e as fontes (chunks) utilizadas para gerá-la.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a base de conhecimento foi populada manualmente, quando eu envio uma requisição `POST` para `/query` com a pergunta "Como funciona a ingestão?", então eu recebo um status `200 OK` e um corpo JSON contendo uma chave `answer` com a resposta e uma chave `sources` com uma lista de documentos fonte.
    * **AC 2:** Dado que o serviço está no ar, quando eu envio uma requisição `POST` para `/query` sem o campo `question`, então eu recebo um status de erro `422 Unprocessable Entity` com uma mensagem clara.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de integração para o endpoint `/query` escritos e passando.
    * [ ] Funcionalidade validada manualmente com uma ferramenta de API (como curl ou Postman).
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Criaremos um novo router no FastAPI para gerenciar as consultas. O endpoint irá orquestrar a lógica, primeiro chamando um serviço de recuperação para buscar o contexto no Neo4j e, em seguida, passando esse contexto para um serviço de geração que interage com o Ollama.
* **Backend:**
    * - **API:** Criar novo endpoint `POST /api/v1/query` no FastAPI.
    * - **Modelos de Dados:** Definir modelos Pydantic para a requisição (`QueryRequest`) e a resposta (`QueryResponse`).
    * - **Lógica de Recuperação:** Implementar uma função/classe em `src/retrieval/` que:
        * Recebe a pergunta do usuário.
        * Gera o embedding da pergunta usando o modelo `nomic-embed-text` via Ollama.
        * Executa uma busca por similaridade vetorial no Neo4j para encontrar os `Chunks` mais relevantes.
    * - **Lógica de Geração:** Implementar uma função/classe em `src/generation/` que:
        * Recebe a pergunta original e os chunks recuperados.
        * Monta um prompt formatado para o LLM.
        * Chama o modelo `qwen2:8b` via Ollama para gerar a resposta.
* **Frontend:**
    * - Nenhuma implementação de frontend nesta fase. A validação será feita diretamente na API.
* **Banco de Dados:**
    * - Nenhuma alteração de schema necessária. A história depende de um schema e um índice vetorial que serão criados pela História 2.
    * - A consulta de busca vetorial em Cypher será algo como: `CALL db.index.vector.queryNodes('chunks_vector_index', 5, $embedding) YIELD node, score`.
* **Questões em Aberto / Riscos:**
    * - **Latência:** A combinação da busca vetorial e da inferência do LLM pode ser lenta. Precisamos monitorar o tempo de resposta total.
    * - **Qualidade do Prompt:** O template do prompt inicial para o LLM será uma primeira versão. É provável que precise de refinamento contínuo para melhorar a qualidade das respostas.
    * - **Dependência:** O serviço Ollama precisa estar rodando e acessível para a API. A falha de comunicação precisa ser tratada adequadamente.

---
### História 2: Script Manual para Ingestão de Documentos
* **Tipo:** Técnica / Habilitadora

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero executar um script de linha de comando para popular a base de conhecimento com um documento `.txt`, para que haja dados disponíveis para serem consultados pela API de `query`.
* **Requisitos / Detalhes:**
    * O script deve ser criado em `scripts/ingest_documents.py`.
    * O script deve aceitar o caminho de um arquivo `.txt` como argumento.
    * Ele deve ler, dividir o texto em chunks, gerar embeddings para cada chunk e salvá-los no Neo4j.
    * O script deve ser idempotente na criação do índice vetorial (se já existir, não deve falhar).
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que tenho um arquivo `exemplo.txt`, quando executo `python scripts/ingest_documents.py --file ./exemplo.txt` no terminal, então o script termina com sucesso e os nós do tipo `Chunk` correspondentes ao conteúdo do arquivo são criados no Neo4j.
    * **AC 2:** Dado que o banco de dados está vazio, quando executo o script pela primeira vez, então um índice vetorial chamado `chunks_vector_index` é criado no Neo4j para os nós `Chunk`.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Script foi executado com sucesso em um ambiente de desenvolvimento.
    * [ ] Os dados inseridos no Neo4j foram verificados manualmente.
    * [ ] O script contém documentação de uso (comentários ou README).

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Desenvolver um script Python utilizando a biblioteca `argparse` para gerenciar os argumentos de linha de comando. O script irá encapsular todo o pipeline de ingestão: carregar, dividir, gerar embeddings e salvar.
* **Backend:**
    * - **Script:** Criar o arquivo `scripts/ingest_documents.py`.
    * - **Carregador de Documento:** Usar `langchain.document_loaders` para carregar o arquivo `.txt`.
    * - **Divisor de Texto:** Usar `langchain.text_splitter.RecursiveCharacterTextSplitter` para dividir o documento em chunks.
    * - **Geração de Embeddings:** Reutilizar (ou criar) o serviço que se comunica com o Ollama para gerar embeddings para cada chunk.
    * - **Persistência:** Usar o driver do Neo4j para:
        * Executar `CREATE VECTOR INDEX chunks_vector_index IF NOT EXISTS FOR (c:Chunk) ON (c.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 768, `vector.similarity_function`: 'cosine'}}`.
        * Criar os nós `:Chunk` com as propriedades `text` e `embedding`.
* **Frontend:**
    * - N/A.
* **Banco de Dados:**
    * - O script será responsável por definir e criar o índice vetorial necessário para a busca por similaridade.
    * - O modelo de dados inicial será um nó simples `:Chunk` com as propriedades `text` e `embedding`.
* **Questões em Aberto / Riscos:**
    * - **Configuração:** As configurações (URL do Neo4j, nome do modelo de embedding) devem ser externalizadas para um arquivo `.env` em vez de estarem hardcoded no script.
    * - **Performance:** A geração de embeddings para documentos grandes pode ser demorada. O script deve logar o progresso para o usuário. Risco baixo para esta fase inicial.

---