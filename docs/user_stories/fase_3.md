## Refinamento Colaborativo: Histórias da Fase 3: A Interface de Chat na Web

---
### História 1: Interface de Chat na Web para Consultas RAG
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário Final, eu quero interagir com o sistema através de uma interface de chat na web, para que eu possa fazer perguntas em linguagem natural e receber respostas de forma fácil e intuitiva.
* **Requisitos / Detalhes:**
    * Uma nova página web deve ser criada usando Streamlit para servir como a interface de consulta (`src/ui/pages/02_query_interface.py`).
    * A interface deve apresentar um campo de entrada de texto, sempre visível, para o usuário digitar suas perguntas.
    * Ao submeter uma pergunta, a pergunta do usuário e a resposta do sistema devem ser exibidas em um formato de conversa (chat).
    * O histórico da conversa deve ser mantido e exibido na tela durante a sessão do usuário.
    * Um indicador visual (como um "spinner" ou mensagem de "pensando...") deve ser exibido enquanto o sistema processa a resposta.
    * A interface deve se comunicar com o endpoint de backend `POST /query` (criado na Fase 1) para obter as respostas.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a aplicação web está rodando, quando eu acesso a página de consulta, então eu vejo um título e uma caixa de entrada de texto para iniciar o chat.
    * **AC 2:** Dado que estou na página de chat, quando eu digito uma pergunta e a envio, então a minha pergunta aparece imediatamente na área de conversa, um indicador de carregamento é exibido, e em seguida a resposta do sistema aparece logo abaixo.
    * **AC 3:** Dado que eu já fiz uma pergunta e recebi uma resposta, quando eu faço uma segunda pergunta, então a nova interação (pergunta e resposta) é adicionada ao final da conversa, preservando o histórico anterior na tela.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes manuais de ponta a ponta foram realizados (digitar pergunta, receber resposta, manter histórico).
    * [ ] A interface lida de forma graciosa com o estado de carregamento.
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Utilizaremos o framework Streamlit para construir a interface de usuário. O estado da conversa será gerenciado pelo `st.session_state` do Streamlit. A comunicação com o backend será encapsulada em uma classe de cliente API para manter o código da UI limpo.
* **Backend:**
    * - Nenhuma alteração é necessária no backend. O endpoint `POST /api/v1/query` existente será consumido por esta nova interface.
* **Frontend (Streamlit UI):**
    * - **Arquivo Principal:** Implementar a lógica da página em `src/ui/pages/02_query_interface.py`.
    * - **Gerenciamento de Estado:**
        * Usar `st.session_state` para armazenar o histórico da conversa. No início da execução do script, verificar se `st.session_state.messages` existe; se não, inicializá-lo como uma lista vazia.
    * - **Componentes da UI:**
        * Iterar sobre a lista de mensagens no `st.session_state` e usar `st.chat_message(role)` para exibir cada mensagem (do "user" e do "assistant").
        * Usar `st.chat_input("Faça sua pergunta")` para capturar a entrada do usuário.
    * - **Comunicação com API:**
        * Criar um helper ou uma classe `RAGClient` em `src/api/client.py`. Este cliente usará a biblioteca `requests` para fazer a chamada `POST` para o backend.
        * Na página Streamlit, ao receber uma nova pergunta do usuário:
            1. Adicionar a pergunta do usuário ao `st.session_state.messages` e redesenhar a tela.
            2. Mostrar um `st.spinner("Processando...")`.
            3. Chamar o `RAGClient` para obter a resposta do backend.
            4. Adicionar a resposta do assistente ao `st.session_state.messages` e redesenhar a tela novamente.
* **Banco de Dados:**
    * - Nenhuma interação direta. A UI é desacoplada do banco de dados.
* **Questões em Aberto / Riscos:**
    * - **Tratamento de Erros na UI:** O que acontece se a chamada para a API falhar? O `RAGClient` deve capturar exceções (ex: `ConnectionError`, status HTTP 5xx) e a UI deve exibir uma mensagem de erro amigável na interface de chat (e.g., "Desculpe, não consegui processar sua pergunta. Tente novamente.").
    * - **Configuração da URL da API:** A URL do backend não deve ser hardcoded na UI. Deve ser lida de uma variável de ambiente para que a aplicação Streamlit possa apontar para diferentes ambientes de backend (local, staging).

---