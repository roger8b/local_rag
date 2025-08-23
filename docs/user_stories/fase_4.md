## Refinamento Colaborativo: Histórias da Fase 4: Upload de Documentos pela Web

---
### História 1: Interface Web para Upload de Documentos
* **Tipo:** Funcional

#### Parte 1: Especificação Funcional (Visão do Product Owner)
* **História de Usuário:** Como um Usuário Final, eu quero fazer o upload de meus próprios documentos de texto (`.txt`) através da interface web, para que eu possa expandir a base de conhecimento do sistema com minhas próprias informações sem depender de um desenvolvedor.
* **Requisitos / Detalhes:**
    * Deve ser criada uma nova página na aplicação web dedicada ao upload de documentos (`src/ui/pages/01_document_upload.py`).
    * A página deve conter um componente de upload de arquivos que permita ao usuário selecionar um arquivo `.txt` de seu computador.
    * Após o usuário selecionar um arquivo e iniciar o envio, a interface deve enviar este arquivo para o endpoint de backend `POST /ingest`.
    * O usuário deve receber feedback visual claro sobre o status do processo (ex: aguardando envio, enviando, sucesso, falha).
    * Uma vez que o upload seja bem-sucedido, o usuário deve ser notificado de que o documento foi processado e está pronto para ser consultado.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado que estou na página de upload, quando eu seleciono um arquivo `.txt` e clico em "Enviar", então o arquivo é enviado para o backend e eu vejo uma mensagem de sucesso na tela, como "Documento enviado com sucesso!".
    * **AC 2:** Dado que eu acabei de fazer o upload de um novo documento com sucesso, quando eu navego para a página de chat e faço uma pergunta sobre o conteúdo específico daquele documento, então eu recebo uma resposta relevante.
    * **AC 3:** Dado que estou na página de upload, quando tento selecionar um arquivo de um formato não permitido (ex: `.jpg`), então o componente de upload deve restringir a seleção apenas para arquivos `.txt`.
* **Definição de 'Pronto' (DoD Checklist):**
    * [ ] Código revisado por um par (PR aprovado).
    * [ ] Testes manuais de ponta a ponta foram realizados (selecionar arquivo, enviar, verificar mensagem, consultar no chat).
    * [ ] A interface fornece feedback adequado ao usuário durante e após o upload.
    * [ ] Não introduziu bugs de regressão.

#### Parte 2: Especificação Técnica (Visão do Engenheiro)
* **Abordagem Técnica Proposta:**
    * Criaremos uma nova página Streamlit que utilizará o componente `st.file_uploader` para a seleção de arquivos. A lógica de comunicação com a API, já encapsulada no `RAGClient`, será estendida para suportar o envio de arquivos a partir da interface web.
* **Backend:**
    * - Nenhuma alteração é necessária no backend. O endpoint `POST /api/v1/ingest`, desenvolvido na Fase 2, será consumido por esta nova página da interface.
* **Frontend (Streamlit UI):**
    * - **Arquivo Principal:** Criar e implementar a página em `src/ui/pages/01_document_upload.py`.
    * - **Componentes da UI:**
        * Utilizar `st.file_uploader` para o widget de upload. É crucial configurar o parâmetro `type=['txt']` para restringir a seleção de arquivos pelo navegador do cliente.
        * Adicionar um `st.button("Enviar Documento")` que ficará habilitado apenas quando um arquivo for selecionado.
    * - **Comunicação com API:**
        * Estender a classe `RAGClient` (de `src/api/client.py`) para incluir um método `upload_file(file_bytes, filename)`.
        * Este método será responsável por construir e enviar a requisição `POST multipart/form-data` para o endpoint `/ingest`, similar ao que o script CLI da Fase 2 fazia, mas usando os bytes do arquivo recebido pelo Streamlit.
    * - **Lógica da Página:**
        1. O `st.file_uploader` armazena o arquivo enviado em memória.
        2. Quando o botão "Enviar" é pressionado, a aplicação chama o método `upload_file` do `RAGClient`.
        3. A interface exibe um `st.spinner("Processando documento...")` enquanto aguarda a resposta da API.
        4. O resultado da chamada (sucesso ou falha) é exibido ao usuário usando `st.success()` ou `st.error()`.
* **Banco de Dados:**
    * - Nenhuma interação direta. A UI permanece completamente desacoplada da camada de persistência.
* **Questões em Aberto / Riscos:**
    * - **Feedback de Processamento Lento:** Como a ingestão no backend é síncrona, o usuário na UI ficará aguardando com um spinner. Se o processamento for muito longo (documentos grandes), a experiência do usuário pode ser ruim. Para esta fase, é aceitável, mas o risco deve ser notado para futuras melhorias (ex: sistema de notificação ou polling).
    * - **Limites de Tamanho de Arquivo:** O Streamlit possui uma configuração `server.maxUploadSize` (padrão de 200MB) que limita o tamanho do upload. Embora seja improvável que um arquivo `.txt` atinja esse limite, é um fator a ser considerado.

---