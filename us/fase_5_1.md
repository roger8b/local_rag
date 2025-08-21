## Fase 5: Aprimoramento da Experiência do Usuário (UX)

---

### História 1: Seleção Dinâmica de Modo e Modelo na Interface

*   **Tipo:** Feature / UX

#### Parte 1: Especificação Funcional (Visão do Product Owner)

*   **História de Usuário:** Como um **Usuário Final**, eu quero **selecionar dinamicamente o modo de operação (Consulta ou Ingestão) e o provedor/modelo de LLM diretamente na interface gráfica**, para que eu possa **alternar entre tarefas e experimentar diferentes modelos de forma rápida e intuitiva, sem precisar reiniciar a aplicação ou editar arquivos de configuração**.
*   **Requisitos / Detalhes:**
    *   A interface principal (Streamlit) deve apresentar uma barra lateral (`sidebar`) persistente com as opções de configuração.
    *   Na barra lateral, o usuário deve poder escolher o **Modo de Operação** através de um seletor (ex: botões de rádio) com as opções: "Consulta" e "Ingestão".
    *   A interface principal deve mudar dinamicamente para exibir a página de consulta ou a página de upload de documentos, com base no modo selecionado.
    *   A barra lateral deve conter um seletor para o **Provedor de LLM** (ex: "Local (Ollama)", "OpenAI").
    *   Abaixo do seletor de provedor, um segundo seletor para o **Modelo** deve ser exibido. A lista de modelos neste seletor deve ser atualizada dinamicamente com base no provedor escolhido.
    *   Ao selecionar um provedor, um modelo padrão (default) recomendado para ele deve ser pré-selecionado automaticamente, agilizando a interação.
    *   As seleções do usuário devem ser usadas em todas as chamadas subsequentes para a API de ingestão ou consulta.
*   **Critérios de Aceite (ACs):**
    *   **AC 1:** Dado que a aplicação está no ar, quando eu seleciono o modo "Consulta", a interface de chat é exibida. Quando eu seleciono o modo "Ingestão", a interface de upload de arquivos é exibida.
    *   **AC 2:** Dado que selecionei o provedor "Local (Ollama)", quando clico no seletor de "Modelo", então a lista de modelos disponíveis na minha instância local do Ollama é exibida.
    *   **AC 3:** Dado que selecionei o provedor "OpenAI" e o modelo "gpt-4-turbo", quando eu envio uma pergunta na interface de "Consulta", então a API de backend é chamada com os parâmetros corretos para usar o provedor e modelo da OpenAI.
    *   **AC 4:** Dado que o modelo padrão para "Local (Ollama)" está configurado como "qwen2:8b", quando eu seleciono o provedor "Local (Ollama)", então o seletor de "Modelo" é populado e "qwen2:8b" já aparece como a opção selecionada.
*   **Definição de 'Pronto' (DoD Checklist):**
    *   [ ] Código revisado por um par (PR aprovado).
    *   [ ] Testes de unidade/integração para os novos componentes de UI e lógica de backend escritos e passando.
    *   [ ] Funcionalidade validada manualmente no Streamlit em um ambiente de desenvolvimento.
    *   [ ] A interface responde de forma graciosa se um provedor (ex: Ollama) estiver offline.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)

*   **Abordagem Técnica Proposta:**
    *   Refatorar a aplicação Streamlit para introduzir uma barra lateral (`st.sidebar`) como o principal centro de controle. Utilizaremos o `st.session_state` para manter o estado das seleções do usuário (modo, provedor, modelo) de forma persistente entre as interações. O backend será modificado para receber e honrar essas seleções.
*   **Backend:**
    *   - **Configuração:** Definir os modelos padrão para cada provedor no arquivo de configuração `settings.py` (ex: `OLLAMA_DEFAULT_MODEL`, `OPENAI_DEFAULT_MODEL`).
    *   - **Serviços:** Modificar as assinaturas dos métodos em `IngestionService` e no serviço de consulta para aceitar `provider` e `model_name` como parâmetros.
    *   - **API:** Atualizar os endpoints `POST /query` e `POST /ingest` para aceitar os novos campos `provider` and `model_name` no corpo da requisição.
    *   - **Provedores:** Implementar uma nova funcionalidade no backend (possivelmente um endpoint `GET /models/{provider}`) que retorna a lista de modelos disponíveis e o modelo padrão.
        *   A resposta da API deve ser um JSON no formato: `{"models": ["model1", "model2"], "default": "model1"}`.
        *   Para "ollama", fará uma chamada HTTP para o endpoint `/api/tags` do Ollama e buscará o padrão do `settings.py`.
        *   Para "openai", pode retornar uma lista estática e o padrão definidos no arquivo de configurações (`settings.py`).
*   **Frontend (Streamlit):**
    *   - **Estrutura:** Usar `st.sidebar` para conter os seletores.
    *   - **Seletores:**
        *   `st.radio` para a seleção de "Modo de Operação".
        *   `st.selectbox` para a seleção de "Provedor".
        *   `st.selectbox` para a seleção de "Modelo".
    *   - **Estado:** Usar `st.session_state` para armazenar as escolhas do usuário.
    *   - **Lógica Dinâmica:**
        *   A seleção do provedor irá disparar uma chamada à API do nosso backend (`GET /models/{provider}`) para popular o seletor de modelos.
        *   O `st.selectbox` de modelos usará o valor do modelo padrão recebido da API para definir sua seleção inicial (usando o parâmetro `index`).
        *   A área principal da página usará um `if/else` baseado em `st.session_state.selected_mode` para renderizar a interface de consulta ou de ingestão.
*   **Banco de Dados:**
    *   - Nenhuma alteração de schema necessária.
*   **Questões em Aberto / Riscos:**
    *   - **Gerenciamento de Estado:** O gerenciamento de estado no Streamlit requer atenção para garantir que os callbacks e o `session_state` funcionem como esperado sem re-renderizações indesejadas.
    *   - **Tratamento de Erros na UI:** A interface precisa lidar de forma elegante com falhas na comunicação com o backend (ex: se a API do Ollama estiver offline ao tentar listar os modelos), exibindo uma mensagem de erro clara para o usuário na barra lateral.
    *   - **Segurança:** Se a seleção de modelos for totalmente dinâmica, garantir que apenas modelos permitidos/testados sejam expostos ou utilizados.

---