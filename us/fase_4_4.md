## Refinamento Colaborativo: Histórias da Fase 3: Flexibilização do Motor de Geração

---
### História 1: Refatoração do Serviço de Geração para Suporte a Múltiplos Provedores de LLM
* **Tipo:** Técnica / Habilitadora

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero refatorar o serviço de geração de texto para que ele possa utilizar diferentes provedores de LLM (Ollama, OpenAI, Google Gemini) de forma intercambiável, para que o sistema se torne mais flexível e possamos otimizar custos e performance escolhendo o melhor modelo para cada cenário.
* **Requisitos / Detalhes:**
    * A seleção do provedor de LLM e de Embedding deve ser centralizada no arquivo de configurações (`src/config/settings.py`).
    * Deve ser possível alterar o provedor em tempo de execução apenas modificando a configuração, sem a necessidade de alterar o código-fonte da aplicação.
    * A implementação atual, que usa Ollama, deve ser mantida e adaptada para funcionar dentro da nova estrutura flexível.
    * O sistema deve lançar um erro claro na inicialização se um provedor configurado não tiver uma implementação correspondente.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que a configuração em `settings.py` especifica `LLM_PROVIDER="ollama"`, quando eu envio uma requisição `POST` para `/query`, então o sistema continua funcionando como antes, utilizando o Ollama para gerar a resposta, e todos os testes existentes continuam passando.
    * **AC 2:** Dado que a configuração em `settings.py` é alterada para um provedor ainda não implementado (e.g., `LLM_PROVIDER="anthropic"`), quando a aplicação tenta iniciar, então ela deve falhar com uma mensagem de erro informativa, como "Provedor de LLM 'anthropic' não suportado".
    * **AC 3:** Dado que a estrutura foi refatorada, quando um novo desenvolvedor analisa o `src/generation/`, então a forma de adicionar um novo provedor de LLM é clara e segue um padrão definido (como implementar uma interface ou herdar de uma classe base).
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de unidade para a lógica de seleção de provedor foram criados e estão passando.
    * [ ] Nenhuma regressão funcional foi introduzida (validado pelos testes de integração existentes).
    * [ ] A configuração foi movida com sucesso para o arquivo `settings.py`.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Aplicar o padrão de projeto **Strategy** ou **Factory**. Criaremos uma interface (classe base abstrata) `LLMProvider` em `src/generation/` que define um contrato comum (e.g., um método `generate(prompt)`). A lógica atual do Ollama será movida para uma classe concreta `OllamaProvider` que implementa essa interface. Um factory ou um bloco `if/elif` no serviço de geração será responsável por instanciar o provedor correto com base na configuração.
* **Backend:**
    * - **Configuração:** Em `src/config/settings.py`, adicionar novas variáveis:
        * `LLM_PROVIDER: Literal["ollama", "openai", "gemini"] = "ollama"`
        * `EMBEDDING_PROVIDER: Literal["ollama", "openai"] = "ollama"`
        * `OPENAI_API_KEY: str = ""`
        * `GOOGLE_API_KEY: str = ""`
    * - **Refatoração:**
        * Criar `src/generation/providers/base.py` com a classe abstrata `LLMProvider`.
        * Criar `src/generation/providers/ollama.py` com a classe `OllamaProvider` que encapsula a lógica existente.
        * Modificar `src/generation/generator.py` para usar o factory que seleciona e instancia o provedor com base em `settings.LLM_PROVIDER`.
    * - **Testes:** Criar `tests/test_generation_providers.py` para testar a lógica do factory e garantir que ele falhe corretamente com configurações inválidas.
* **Frontend:**
    * - N/A.
* **Banco de Dados:**
    * - Nenhuma alteração necessária.
* **Questões em Aberto / Riscos:**
    * - **Gerenciamento de Segredos:** As chaves de API (OpenAI, Google) não devem ser commitadas. O uso de variáveis de ambiente (lidas pelo Pydantic) é obrigatório. Isso deve ser documentado.
    * - **Interface Comum:** Garantir que a interface `LLMProvider` seja genérica o suficiente para acomodar as diferentes respostas e parâmetros dos SDKs da OpenAI e do Google.

---
### História 2: Implementação do Provedor OpenAI para Geração e Embeddings
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero integrar os modelos da OpenAI como uma opção para geração de respostas e criação de embeddings, para que eu possa utilizar seus modelos de ponta e avaliar a relação custo-benefício em comparação com a solução local.
* **Requisitos / Detalhes:**
    * O sistema deve ser capaz de usar um modelo da OpenAI (e.g., `gpt-4o`) para o serviço de geração quando configurado.
    * O sistema deve ser capaz de usar um modelo de embedding da OpenAI (e.g., `text-embedding-3-small`) para os processos de ingestão e consulta.
    * A chave da API da OpenAI deve ser lida a partir das configurações (que por sua vez a lê de uma variável de ambiente).
    * A funcionalidade deve ser testável de ponta a ponta.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que `LLM_PROVIDER="openai"` e uma `OPENAI_API_KEY` válida está configurada, quando eu envio uma `POST` para `/query`, então a resposta é gerada com sucesso pela API da OpenAI.
    * **AC 2:** Dado que `EMBEDDING_PROVIDER="openai"` e uma `OPENAI_API_KEY` válida está configurada, quando eu ingiro um novo documento via `POST` para `/ingest`, então os embeddings dos chunks são gerados pela OpenAI e salvos corretamente no Neo4j.
    * **AC 3:** Dado que a `OPENAI_API_KEY` é inválida ou não foi fornecida, quando o sistema tenta usar um serviço da OpenAI, então ele retorna um erro claro e informativo (e.g., `500 Internal Server Error` com a causa raiz).
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de integração que validam o fluxo com OpenAI (geração e embedding) foram criados e estão passando (podem necessitar de mocks para a API externa).
    * [ ] A dependência do cliente Python da OpenAI foi adicionada ao `requirements.txt`.
    * [ ] A documentação de configuração (`configuration.md` ou `README.md`) foi atualizada para explicar como usar o provedor OpenAI.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Criar novas classes `OpenAIProvider` (para LLM) e `OpenAIEmbeddingProvider` que implementam as respectivas interfaces definidas na História 1. Essas classes irão encapsular as chamadas ao SDK da OpenAI.
* **Backend:**
    * - **Dependências:** Adicionar `openai` ao `requirements.txt`.
    * - **Implementação do LLM:**
        * Criar `src/generation/providers/openai.py`.
        * Implementar a classe `OpenAIProvider` herdando de `LLMProvider`.
        * O método `generate` irá instanciar o cliente da OpenAI, fazer a chamada para `client.chat.completions.create()` e formatar a resposta.
    * - **Implementação do Embedding:**
        * (Assumindo uma refatoração similar para embeddings) Criar `src/retrieval/embedding_providers/openai.py`.
        * Implementar a classe `OpenAIEmbeddingProvider` que chama `client.embeddings.create()`.
    * - **Atualização do Factory:** Adicionar a lógica no factory de serviços para instancionar as classes da OpenAI quando `settings.LLM_PROVIDER` ou `settings.EMBEDDING_PROVIDER` for `"openai"`.
* **Frontend:**
    * - N/A.
* **Banco de Dados:**
    * - Nenhuma alteração de schema.
* **Questões em Aberto / Riscos:**
    * - **Custo:** Chamadas à API da OpenAI incorrem em custos. Os testes de integração devem usar mocks para evitar chamadas reais no pipeline de CI/CD.
    * - **Rate Limiting:** As APIs externas têm limites de taxa. Adicione controle de retry e deixe configuravel para evitar problemas.

---
### História 3: Implementação do Provedor Google Gemini para Geração de Respostas
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Desenvolvedor, eu quero integrar os modelos do Google Gemini como uma opção para geração de respostas, para que eu possa utilizar seus modelos avançados e comparar performance/custo com outras soluções disponíveis.
* **Requisitos / Detalhes:**
    * O sistema deve ser capaz de usar um modelo do Google Gemini (e.g., `gemini-2.0-flash-exp`) para o serviço de geração quando configurado.
    * A chave da API do Google deve ser lida a partir das configurações (que por sua vez a lê de uma variável de ambiente).
    * A funcionalidade deve ser testável de ponta a ponta.
    * O provider deve manter compatibilidade com a interface existente.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que `LLM_PROVIDER="gemini"` e uma `GOOGLE_API_KEY` válida está configurada, quando eu envio uma `POST` para `/query`, então a resposta é gerada com sucesso pela API do Google Gemini.
    * **AC 2:** Dado que a `GOOGLE_API_KEY` é inválida ou não foi fornecida, quando o sistema tenta usar o serviço do Gemini, então ele retorna um erro claro e informativo (e.g., `500 Internal Server Error` com a causa raiz).
    * **AC 3:** Dado que o factory foi atualizado, quando o sistema é configurado para usar Gemini, então a resposta é gerada sem modificar outros componentes do sistema.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes de integração que validam o fluxo com Google Gemini foram criados e estão passando (podem necessitar de mocks para a API externa).
    * [ ] A dependência do cliente Python do Google Generative AI foi adicionada ao `requirements.txt`.
    * [ ] A documentação de configuração foi atualizada para explicar como usar o provedor Gemini.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Criar nova classe `GeminiProvider` que implementa a interface `LLMProvider` definida na arquitetura. Esta classe irá encapsular as chamadas ao SDK do Google Generative AI.
* **Backend:**
    * - **Dependências:** Adicionar `google-generativeai` ao `requirements.txt`.
    * - **Implementação do LLM:**
        * Criar `src/generation/providers/gemini.py`.
        * Implementar a classe `GeminiProvider` herdando de `LLMProvider`.
        * O método `generate_response` irá instanciar o cliente do Gemini, fazer a chamada para `model.generate_content()` e formatar a resposta.
        * Usar o modelo `gemini-2.0-flash-exp` conforme configurado.
    * - **Atualização do Factory:** Atualizar a lógica no factory de serviços para instanciar a classe `GeminiProvider` quando `settings.LLM_PROVIDER` for `"gemini"`.
* **Frontend:**
    * - N/A.
* **Banco de Dados:**
    * - Nenhuma alteração de schema.
* **Questões em Aberto / Riscos:**
    * - **Custo:** Chamadas à API do Google Gemini incorrem em custos. Os testes de integração devem usar mocks para evitar chamadas reais no pipeline de CI/CD.
    * - **Rate Limiting:** As APIs externas têm limites de taxa. Adicionar controle de retry e tratamento de erros configurável.
    * - **Modelos Disponíveis:** Verificar disponibilidade do modelo `gemini-2.0-flash-exp` e ter fallback se necessário.

---
### História 4: Seleção Dinâmica de Provider LLM via Interface e API
* **Tipo:** Funcional / UX

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário do sistema RAG, eu quero poder escolher qual provider LLM usar para cada consulta individual (Ollama, OpenAI, ou Gemini), para que eu possa comparar respostas, otimizar custos por pergunta, e ter flexibilidade total sobre qual modelo usar sem precisar reconfigurar o sistema.
* **Requisitos / Detalhes:**
    * A interface Streamlit deve ter um seletor visual para escolher o provider antes de fazer uma pergunta.
    * A API deve aceitar um parâmetro opcional `provider` no request para sobrescrever a configuração padrão.
    * O sistema deve mostrar qual provider foi usado na resposta (tanto na UI quanto na API).
    * Deve haver fallback para o provider padrão caso o especificado não esteja disponível.
    * A funcionalidade deve permitir comparação lado a lado entre providers.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que estou na interface Streamlit, quando eu seleciono "OpenAI" no dropdown de providers e faço uma pergunta, então a resposta é gerada usando OpenAI e o sistema indica claramente qual provider foi usado.
    * **AC 2:** Dado que envio um `POST` para `/query` com `{"question": "teste", "provider": "gemini"}`, quando o sistema processa a requisição, então a resposta é gerada usando Gemini independente da configuração padrão do arquivo `.env`.
    * **AC 3:** Dado que especifico um provider inválido (e.g., `"anthropic"`), quando o sistema processa a requisição, então ele retorna um erro claro listando os providers disponíveis.
    * **AC 4:** Dado que especifico um provider que requer API key não configurada, quando o sistema tenta usar esse provider, então retorna erro informativo sobre a configuração necessária.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Interface Streamlit atualizada com seletor de provider.
    * [ ] API aceita parâmetro `provider` opcional.
    * [ ] Respostas incluem indicação do provider usado.
    * [ ] Testes cobrindo todos os cenários de seleção dinâmica.
    * [ ] Documentação atualizada explicando a nova funcionalidade.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Modificar o modelo `QueryRequest` para incluir campo opcional `provider`.
    * Criar função `create_llm_provider_dynamic()` que aceita provider como parâmetro.
    * Atualizar interface Streamlit com `st.selectbox` para escolha de provider.
    * Implementar validação e tratamento de erros para providers indisponíveis.
* **Backend:**
    * - **Modelos de API:**
        * Atualizar `src/models/api_models.py`:
            * Adicionar `provider: Optional[Literal["ollama", "openai", "gemini"]] = None` em `QueryRequest`.
            * Adicionar `provider_used: str` em `QueryResponse`.
    * - **Lógica de Seleção:**
        * Modificar `src/generation/generator.py`:
            * Criar `create_llm_provider_dynamic(provider_override: Optional[str] = None)`.
            * Implementar lógica de fallback e validação.
        * Atualizar endpoint `/query` para usar o novo parâmetro.
    * - **Validação:**
        * Implementar validação de provider disponível.
        * Verificar configuração de API keys necessárias.
        * Retornar erros informativos com lista de providers válidos.
* **Frontend (Streamlit):**
    * - **Seletor de Provider:**
        * Adicionar `st.selectbox` com opções: ["Auto (padrão)", "Ollama", "OpenAI", "Gemini"].
        * Mostrar status de configuração (🟢 configurado, 🔴 não configurado) ao lado de cada opção.
    * - **Indicação de Provider Usado:**
        * Exibir badge ou tag mostrando qual provider gerou a resposta.
        * Adicionar métricas de tempo de resposta por provider.
    * - **Modo Comparação (Futuro):**
        * Interface para comparar respostas de múltiplos providers lado a lado.
* **Banco de Dados:**
    * - Nenhuma alteração necessária.
* **Questões em Aberto / Riscos:**
    * - **Performance:** Chamadas para múltiplos providers simultaneamente podem impactar performance.
    * - **Custo:** Facilitar mudança de provider pode aumentar uso inadvertido de APIs pagas.
    * - **UX:** Interface deve ser clara sobre quais providers estão configurados e funcionais.
    * - **Caching:** Considerar se cache de respostas deve ser por provider ou compartilhado.
