### História 2: Log Detalhado de Atividades na Interface

*   **Tipo:** Feature / UX

#### Parte 1: Especificação Funcional (Visão do Product Owner)

*   **História de Usuário:** Como um **Usuário Final**, eu quero **ver um log detalhado e em tempo real das etapas de processamento diretamente na interface** quando eu realizo uma ação (ingestão ou consulta), para que eu possa **acompanhar o progresso, entender o que o sistema está fazendo e diagnosticar problemas rapidamente**.
*   **Requisitos / Detalhes:**
    *   Em ambas as interfaces de "Consulta" e "Ingestão", deve haver uma área designada, como uma seção expansível (`expander`), chamada "Detalhes do Processamento".
    *   Ao iniciar uma ação (enviar uma pergunta ou um arquivo), esta seção deve exibir mensagens de status que descrevem cada etapa do processo.
    *   **Para Ingestão, os logs devem incluir:**
        *   Validação do arquivo.
        *   Início e fim da divisão em chunks (ex: "Texto dividido em 42 chunks.").
        *   Início da geração de embeddings (ex: "Gerando embeddings com o provedor 'OpenAI' usando o modelo 'text-embedding-3-small'...").
        *   Confirmação de persistência no banco de dados.
        *   Tempo decorrido para etapas críticas (ex: "Embeddings gerados em 15.3s.").
        *   Mensagem final de sucesso ou de erro.
    *   **Para Consulta, os logs devem incluir:**
        *   Geração do embedding da pergunta.
        *   Busca vetorial no banco de dados (ex: "Busca vetorial retornou 5 chunks relevantes em 0.8s.").
        *   Início da geração da resposta final (ex: "Enviando contexto para o LLM 'gpt-4-turbo'...").
        *   Mensagem de sucesso.
*   **Critérios de Aceite (ACs):**
    *   **AC 1:** Dado que estou na página de "Ingestão", quando faço o upload de um arquivo `.txt`, então eu posso expandir a seção "Detalhes do Processamento" e ver uma lista de logs sequenciais descrevendo as etapas de chunking, embedding e salvamento.
    *   **AC 2:** Dado que estou na página de "Consulta", quando envio uma pergunta, então a seção de detalhes exibe as etapas de busca vetorial e geração de resposta, incluindo os modelos utilizados.
    *   **AC 3:** Dado que ocorre um erro durante o processo (ex: o Neo4j está offline), então uma mensagem de erro clara e informativa é exibida na seção de logs, em vez de falhar silenciosamente.
*   **Definição de 'Pronto' (DoD Checklist):**
    *   [ ] Código revisado por um par (PR aprovado).
    *   [ ] A nova funcionalidade de log está presente e funcional em ambas as páginas (Consulta e Ingestão).
    *   [ ] Funcionalidade validada manualmente no Streamlit.
    *   [ ] Os logs são claros, concisos e fáceis de entender para um usuário não-técnico.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)

*   **Abordagem Técnica Proposta:**
    *   A abordagem mais simples e robusta, sem a complexidade de streaming, é fazer com que os serviços de backend coletem uma lista de eventos de log durante sua execução. Essa lista de logs será então retornada como parte da resposta final da API, e o frontend se encarregará de renderizá-la de uma vez.
*   **Backend:**
    *   - **Serviços:** Modificar os métodos principais (ex: `ingest_from_content` em `IngestionService`) para que, em vez de apenas logar no console, eles também construam e retornem uma lista de mensagens de log estruturadas.
    *   - **Estrutura do Log:** Cada entrada na lista de logs pode ser um dicionário com nível, mensagem e tempo (ex: `{"level": "info", "message": "Texto dividido em 42 chunks.", "duration_ms": 50}`).
    *   - **API:** Modificar as respostas dos endpoints `/query` e `/ingest` para incluir um novo campo `logs` no JSON de retorno. A resposta ficaria no formato: `{"data": {...}, "logs": [...]}`.
*   **Frontend (Streamlit):**
    *   - **Componente de UI:** Utilizar `st.expander("Detalhes do Processamento")` para criar a seção de log recolhível.
    *   - **Renderização:** Após receber a resposta da API, o frontend irá verificar a presença do campo `logs`.
    *   - Se `logs` existir, o frontend irá iterar sobre a lista e renderizar cada mensagem. Pode-se usar `st.info()`, `st.success()`, `st.warning()`, `st.error()` com base no campo `level` de cada log.
    *   - Opcionalmente, usar `st.spinner()` enquanto a operação de backend está em andamento, com uma mensagem genérica como "Processando...". Ao final, o spinner é substituído pelo resultado e pelos logs detalhados.
*   **Banco de Dados:**
    *   - Nenhuma alteração de schema necessária.
*   **Questões em Aberto / Riscos:**
    *   - **Granularidade do Log:** Definir o nível de detalhe ideal para os logs é um equilíbrio. Muitos logs podem poluir a interface, enquanto poucos logs podem não ser úteis. Começaremos com as etapas macro.
    *   - **Acoplamento:** Os serviços de backend ficarão um pouco mais acoplados à apresentação, pois estarão gerando mensagens para a UI. Manter as mensagens de log claras e baseadas em fatos (em vez de texto de marketing) mitigará esse risco.

---