## Refinamento Colaborativo: História da Fase 4.1: Implementação do Provedor de Embedding Remoto (OpenAI)

---
### História 1: Finalizar Implementação do Provedor de Embedding OpenAI

* **Tipo:** Funcional
* **Problema:** A interface do usuário permite selecionar OpenAI como provedor de embeddings, mas o backend não processa essa escolha, utilizando sempre o provedor local (Ollama).

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário, eu quero que a minha escolha de usar o provedor de embeddings "OpenAI" na tela de upload seja respeitada pelo sistema, para que eu possa me beneficiar de um processamento de documentos mais rápido quando necessário.
* **Requisitos / Detalhes:**
    * A interface de upload de documentos deve enviar a escolha do provedor de embedding (Ollama ou OpenAI) para o backend.
    * A seleção do provedor na interface deve ser refatorada para ser mais escalável, permitindo a fácil adição de novos provedores (como Gemini) no futuro.
    * O endpoint da API de ingestão de documentos deve ser capaz de receber e interpretar essa escolha.
    * Se "OpenAI" for escolhido, o serviço de ingestão deve usar a API da OpenAI para gerar os embeddings.
    * Se "Local (Ollama)" for escolhido, o comportamento atual deve ser mantido.
    * A configuração da chave de API da OpenAI (`OPENAI_API_KEY`) deve ser usada pelo backend ao se comunicar com a OpenAI.
    * O sistema deve fornecer feedback claro ao usuário caso a API da OpenAI seja escolhida mas a chave não esteja configurada ou seja inválida.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a chave da API da OpenAI está configurada corretamente, quando eu seleciono "☁️ OpenAI" na UI e faço o upload de um documento, então o sistema deve usar a API da OpenAI para gerar os embeddings, e o documento deve ser salvo com sucesso.
    * **AC 2:** Dado que a chave da API da OpenAI **não** está configurada, quando eu seleciono "☁️ OpenAI" e tento fazer o upload, então a API deve retornar um erro `400 Bad Request` com uma mensagem clara indicando que a chave é necessária.
    * **AC 3:** Quando eu seleciono "🏠 Local (Ollama)" e faço o upload de um documento, então o sistema deve usar o Ollama para gerar os embeddings, como já funciona atualmente.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de integração escritos para o serviço de ingestão, cobrindo ambos os provedores (Ollama e OpenAI).
    * [ ] Funcionalidade validada manualmente através da interface do usuário.
    * [ ] A documentação (README.md) foi atualizada para refletir a funcionalidade completa.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Modificaremos a cadeia de chamadas desde o cliente da API até o serviço de ingestão para passar um novo parâmetro que especifica o provedor de embedding. Uma lógica condicional no serviço de ingestão selecionará o cliente apropriado (Ollama ou um novo cliente OpenAI) para gerar os vetores.
* **Frontend (UI):**
    * - **`src/ui/pages/document_upload.py`**: Refatorar o componente de seleção (`st.radio`) para ser gerado dinamicamente a partir de uma estrutura de dados (ex: um dicionário de provedores). A chamada `rag_client.upload_file` deve ser modificada para incluir a chave do provedor selecionado (ex: 'ollama', 'openai').
* **API Client:**
    * - **`src/api/client.py`**: O método `upload_file` precisa ser atualizado para aceitar o parâmetro `embedding_provider` e enviá-lo no corpo da requisição para a API.
* **Backend:**
    * - **API (`src/api/routes.py`):** O endpoint de upload (`/upload`) deve ser atualizado para aceitar um campo opcional no corpo da requisição, por exemplo, `embedding_provider: str = "ollama"`.
    * - **Serviço de Ingestão (`src/application/services/ingestion_service.py`):**
        * O método `ingest_from_content` (ou similar) deve receber o parâmetro `embedding_provider`.
        * A lógica do método `_generate_embeddings` deve ser refatorada. Em vez de chamar diretamente o código do Ollama, ele deve delegar a geração para uma outra classe/função baseada no valor de `embedding_provider`.
        * Criar uma nova implementação para gerar embeddings via OpenAI, que será chamada se `embedding_provider == "openai"`. Esta nova implementação precisará ler a `OPENAI_API_KEY` das configurações.
* **Banco de Dados:**
    * - Nenhuma alteração de schema é necessária. Os embeddings gerados pela OpenAI devem ter a mesma dimensão que os do Ollama, ou o índice vetorial precisará ser reconfigurado (ponto a ser verificado).
* **Questões em Aberto / Riscos:**
    * - **Dimensão dos Embeddings:** É crucial garantir que o modelo de embedding da OpenAI (ex: `text-embedding-3-small`) gere vetores com a mesma dimensão configurada no índice do Neo4j (atualmente 256 para `nomic-embed-text`). Se não for o caso, será necessário um plano de migração ou uma configuração mais complexa. **Ação:** Verificar a dimensão do modelo da OpenAI e ajustar o código ou a configuração do índice.
    * - **Gerenciamento de Erros:** A comunicação com a API da OpenAI pode falhar por diversos motivos (chave inválida, cota excedida, etc.). O tratamento de erros precisa ser robusto.
    * - **Custo:** O uso da API da OpenAI gera custos. A interface deve deixar isso claro para o usuário. (Já está parcialmente feito).
