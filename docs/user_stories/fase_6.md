## Refinamento Colaborativo: Histórias da Fase 6: Gerenciamento da Base de Conhecimento

---
### História 3: Gerenciar Banco de Dados (Status, Índice e Limpeza)
* **Tipo:** Funcional / Admin

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Administrador, quero uma interface simples para ver o status do banco, recriar o índice vetorial e limpar dados de desenvolvimento, para manter a base de conhecimento saudável durante a evolução do produto.
* **Requisitos / Detalhes:**
    * Uma nova página na interface "Gerenciador do Banco" (`src/ui/pages/04_db_manager.py`).
    * Novos endpoints:
        - `GET /api/v1/db/status`: retorna quantidade de documentos, chunks e se o índice vetorial existe.
        - `POST /api/v1/db/reindex`: (re)cria o índice vetorial `document_embeddings`.
        - `DELETE /api/v1/db/clear?confirm=true`: limpa dados de desenvolvimento (remove nós `:Chunk` e índice), com confirmação explícita.
    * A página deve exibir o status atual e oferecer botões para “Recriar índice” e “Limpar base (dev)”.
    * A limpeza deve exigir confirmação visual (ex.: checkbox “Entendo os riscos”).
* **Critérios de Aceite (ACs):**
    * **AC 1:** Ao acessar “Gerenciador do Banco”, vejo contagens de documentos e chunks e se o índice existe.
    * **AC 2:** Ao clicar em “Recriar índice”, recebo feedback de sucesso e o status passa a mostrar o índice existente.
    * **AC 3:** Ao confirmar e clicar em “Limpar base (dev)”, os chunks são apagados e o índice removido.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Endpoints implementados e cobertos por testes.
    * [ ] Página da UI funcional com feedback ao usuário.
    * [ ] Documentação atualizada.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Backend:**
    * `GET /db/status`: Cypher para contagem e `SHOW INDEXES`.
    * `POST /db/reindex`: Reaproveitar lógica de `_ensure_vector_index()` com dimensões de `settings.openai_embedding_dimensions`.
    * `DELETE /db/clear`: Reaproveitar queries do script `scripts/clear_database.py` (dropar índice e `MATCH (n:Chunk) DETACH DELETE n`).
* **Frontend:**
    * Nova página `04_db_manager.py` com `st.metric` para contagens, `st.button` para ações e `st.checkbox` para confirmação.
* **Cliente API:**
    * Métodos `get_db_status()`, `reindex_db()`, `clear_db(confirm: bool)` no `RAGClient`.
* **Banco de Dados:**
    * Sem mudanças de schema.

### História 1: Visualizar Documentos Ingeridos
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário Final, eu quero ver uma lista de todos os documentos que já foram carregados no sistema, para que eu possa ter uma visão geral da base de conhecimento e gerenciar seu conteúdo.
* **Requisitos / Detalhes:**
    * Deve ser criada uma nova página na interface web chamada "Gerenciador de Documentos" (`src/ui/pages/03_document_manager.py`).
    * Um novo endpoint de backend, `GET /documents`, deve ser criado para fornecer a lista de todos os documentos.
    * A lista na interface do usuário deve exibir, para cada documento, informações chave como nome do arquivo, tipo (PDF/TXT) e data de ingestão.
    * A lista deve ser apresentada de forma clara e ordenada, preferencialmente com os documentos mais recentes primeiro.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que vários documentos já foram carregados, quando eu navego para a página "Gerenciador de Documentos", então eu vejo uma tabela ou lista com todos os documentos que foram ingeridos.
    * **AC 2:** Dado que a lista é exibida, para cada item eu consigo identificar claramente o nome do arquivo, seu formato e quando ele foi adicionado ao sistema.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Novo endpoint `GET /documents` foi testado e está retornando os dados esperados.
    * [ ] A nova página da UI está buscando e exibindo os dados corretamente.
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Para viabilizar esta funcionalidade, precisamos evoluir nosso modelo de dados. Introduziremos um nó `:Document` no Neo4j para agrupar os chunks. O processo de ingestão será modificado para criar este nó e relacioná-lo aos seus respectivos chunks. A nova página da UI consumirá um novo endpoint da API que consulta estes nós de documento.
* **Backend:**
    * - **Modificação no Serviço de Ingestão:** O serviço (`ingestion_service.py`) deve ser alterado. Antes de criar os chunks, ele deve criar um nó `:Document` com propriedades como `doc_id` (um UUID gerado), `filename`, `filetype` e `ingested_at`.
    * - **Modificação no Modelo de Dados:** Cada nó `:Chunk` criado a partir do arquivo deve ser conectado ao nó `:Document` correspondente através de uma relação, como `(c:Chunk)-[:PART_OF]->(d:Document)`.
    * - **Nova API:** Criar o endpoint `GET /api/v1/documents`.
    * - **Lógica da API:** O endpoint executará uma consulta Cypher para buscar todos os documentos: `MATCH (d:Document) RETURN d ORDER BY d.ingested_at DESC`.
* **Frontend (Streamlit UI):**
    * - **Nova Página:** Criar o arquivo `src/ui/pages/03_document_manager.py`.
    * - **Cliente API:** Adicionar um novo método `list_documents()` ao `RAGClient` para chamar o novo endpoint `GET /documents`.
    * - **Componentes:** Na nova página, chamar o método do cliente API e usar `st.dataframe()` para exibir os resultados de forma tabular.
* **Banco de Dados:**
    * - **Evolução do Schema:** Requer a adição do nó `:Document` e da relação `:PART_OF`. Esta é a principal alteração técnica da história. Documentos ingeridos antes desta mudança não aparecerão na lista.
* **Questões em Aberto / Riscos:**
    * - **Dados Legados:** Documentos ingeridos antes desta mudança não estarão associados a um nó `:Document`. Precisamos decidir se criamos um script de migração ou se aceitamos que a funcionalidade só se aplicará a novos documentos. Para esta fase, aceitaremos que apenas novos documentos serão gerenciáveis.

---
### História 2: Remover um Documento da Base de Conhecimento
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário Final, eu quero poder remover um documento da base de conhecimento, para que eu possa descartar informações desatualizadas, irrelevantes ou incorretas, mantendo a qualidade das respostas.
* **Requisitos / Detalhes:**
    * Na lista de documentos da página "Gerenciador de Documentos", cada item deve ter uma opção para exclusão (ex: um botão "Remover").
    * Ao clicar em "Remover", o sistema deve pedir uma confirmação ao usuário para evitar exclusões acidentais.
    * Se confirmado, a aplicação deve chamar um endpoint de backend para apagar o documento e todos os seus dados associados (chunks, vetores, etc.).
    * Após a exclusão, a lista de documentos na UI deve ser atualizada, e o item removido não deve mais aparecer.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que estou na página do gerenciador, quando clico no botão "Remover" de um documento, então uma caixa de diálogo de confirmação é exibida.
    * **AC 2:** Dado que eu confirmo a exclusão, quando o processo termina, o documento desaparece da lista e uma notificação de sucesso é exibida.
    * **AC 3:** Dado que um documento foi removido, quando eu tento fazer uma pergunta sobre seu conteúdo na página de chat, o sistema não deve mais usar aquela informação para formular a resposta.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Novo endpoint `DELETE /documents/{doc_id}` foi testado e está removendo os dados corretamente.
    * [ ] A funcionalidade na UI (botão, confirmação, atualização da lista) está funcionando como esperado.
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Adicionaremos uma coluna à nossa exibição de documentos na UI com um botão de exclusão para cada linha. Este botão acionará a chamada a um novo endpoint `DELETE` na API, que por sua vez executará uma consulta Cypher para remover o nó do documento e todos os seus chunks associados.
* **Backend:**
    * - **Nova API:** Criar o endpoint `DELETE /api/v1/documents/{doc_id}`.
    * - **Lógica da API:** O endpoint receberá o `doc_id` como um parâmetro de caminho. Ele executará uma consulta Cypher para encontrar e remover o documento e todos os seus chunks. A consulta será: `MATCH (d:Document {doc_id: $doc_id}) OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk) DETACH DELETE d, c`. O uso de `DETACH DELETE` garante que os nós e suas relações sejam removidos de forma limpa.
* **Frontend (Streamlit UI):**
    * - **Página de Gerenciamento (`03_document_manager.py`):**
        * A exibição da lista precisa ser modificada. Como `st.dataframe` não suporta botões, vamos iterar sobre a lista de documentos e usar `st.columns` para criar uma linha para cada um, com as informações do documento em uma coluna e um `st.button("Remover", key=doc_id)` na outra.
        * A `key` do botão deve ser única para cada documento para que o Streamlit possa diferenciar os cliques.
        * Ao clicar no botão, usamos um `if` para acionar a lógica de exclusão. Dentro do `if`, podemos usar `st.warning` e um segundo botão para a confirmação.
        * Se confirmado, chamar um novo método `delete_document(doc_id)` no `RAGClient`.
        * Após uma resposta bem-sucedida da API, usar `st.success()` para notificar o usuário e `st.experimental_rerun()` (ou `st.rerun()` em versões mais novas) para recarregar a página e atualizar a lista.
* **Banco de Dados:**
    * - Nenhuma mudança no schema, mas a operação é destrutiva. A consulta Cypher é crítica para garantir que não deixemos chunks órfãos no banco de dados.
* **Questões em Aberto / Riscos:**
    * - **Consistência da Exclusão:** A consulta Cypher deve ser robusta para garantir que todos os chunks associados sejam removidos junto com o documento principal. A consulta proposta com `OPTIONAL MATCH` e `DETACH DELETE` é segura e lida com casos onde um documento poderia, hipoteticamente, não ter chunks.

---
