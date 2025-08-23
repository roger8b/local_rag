### História 3: Botão para Limpeza do Banco de Dados na Interface

*   **Tipo:** Feature / Admin

#### Parte 1: Especificação Funcional (Visão do Product Owner)

*   **História de Usuário:** Como um **Desenvolvedor/Administrador**, eu quero um **botão "Limpar Banco de Dados" na interface** para resetar completamente o banco de dados Neo4j, para que eu possa **iniciar rapidamente uma nova sessão de testes ou demonstração com dados limpos**.
*   **Requisitos / Detalhes:**
    *   Deve haver um botão "Limpar Banco de Dados" na barra lateral (`sidebar`) da aplicação.
    *   Devido à natureza destrutiva da ação, ao clicar no botão, o usuário deve ser apresentado a uma **confirmação explícita** para evitar cliques acidentais.
    *   Se a ação for confirmada, a interface deve chamar um novo endpoint no backend que executará a limpeza do banco de dados.
    *   A interface deve exibir uma notificação de sucesso ou erro após a conclusão da operação.
*   **Critérios de Aceite (ACs):**
    *   **AC 1:** Dado que a aplicação está no ar, um botão "Limpar Banco de Dados" é visível na barra lateral.
    *   **AC 2:** Quando eu clico no botão, uma mensagem de aviso e um segundo botão de confirmação (ex: "Sim, limpar tudo") aparecem. A limpeza não ocorre sem este segundo clique.
    *   **AC 3:** Dado que eu confirmei a ação, quando a operação de limpeza termina com sucesso, uma mensagem como "Banco de dados limpo com sucesso!" é exibida na tela.
    *   **AC 4:** Se eu clicar no botão inicial e depois em "Cancelar" (ou simplesmente não confirmar), o banco de dados permanece inalterado.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)

*   **Abordagem Técnica Proposta:**
    *   Criaremos um novo endpoint na API (`POST /database/clear`) dedicado a esta operação. No frontend (Streamlit), adicionaremos o botão e a lógica de confirmação na barra lateral, que fará a chamada para este novo endpoint.
*   **Backend:**
    *   - **API:** Criar um novo endpoint `POST /api/v1/database/clear`.
    *   - **Serviço:** Criar um novo método em um serviço apropriado (ou um novo `DatabaseService`) que encapsula a lógica de limpeza.
    *   - **Lógica de Limpeza:** O método executará as seguintes consultas Cypher, que são mais abrangentes que as do script anterior para garantir uma limpeza completa:
        1.  `DROP INDEX document_embeddings IF EXISTS`
        2.  `MATCH (n) DETACH DELETE n` (Apaga TODOS os nós e relacionamentos).
    *   - **Segurança:** Este endpoint é muito destrutivo. Em um ambiente de produção real, ele deveria ser protegido por autenticação/autorização. Para o escopo atual, vamos mantê-lo aberto no ambiente de desenvolvimento.
*   **Frontend (Streamlit):**
    *   - **Componente de UI:** Adicionar um `st.sidebar.button("Limpar Banco de Dados")` na parte inferior da barra lateral.
    *   - **Lógica de Confirmação:** Usar o `st.session_state` para gerenciar o estado de confirmação.
        *   O clique inicial no botão ativa um flag em `st.session_state`.
        *   Um bloco `if` verificará esse flag e exibirá um `st.sidebar.warning` com o aviso e dois botões: `st.sidebar.button("Confirmar Limpeza")` e `st.sidebar.button("Cancelar")`.
        *   O clique em "Confirmar Limpeza" fará a chamada `POST` para `/api/v1/database/clear` usando `httpx`.
        *   Após a chamada (ou ao clicar em "Cancelar"), o flag no `st.session_state` é resetado para esconder os botões de confirmação.
    *   - **Feedback:** Usar `st.toast`, `st.success` ou `st.error` para mostrar o resultado da operação.
*   **Banco de Dados:**
    *   - As consultas `DROP INDEX` e `MATCH (n) DETACH DELETE n` serão executadas.
*   **Questões em Aberto / Riscos:**
    *   - **Risco de Uso Acidental:** O principal risco é o uso acidental. A UI de confirmação em duas etapas é a principal mitigação.
    *   - **Performance:** Em bancos de dados muito grandes, a operação `MATCH (n) DETACH DELETE n` pode ser lenta e causar um timeout. Para o nosso contexto de desenvolvimento, isso não deve ser um problema.

---