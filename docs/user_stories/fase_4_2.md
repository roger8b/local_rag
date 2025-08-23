## Fase 4.2: Otimização e Eficiência do Pipeline de Ingestão

### Descrição
Após a implementação bem-sucedida dos provedores de embedding local (Ollama) e remoto (OpenAI) na Fase 4.1, esta fase foca em otimizar o pipeline de ingestão. O objetivo é reduzir a latência no processamento de documentos, diminuir o número de chamadas de API e otimizar o uso de recursos de banco de dados e armazenamento. Estas melhorias técnicas visam tornar o sistema mais escalável e com melhor custo-benefício, preparando-o para volumes maiores de dados.

### Histórias

---
### História 1: Otimizar Geração de Embeddings com Ollama via Processamento em Lote (Batch)

* **Tipo:** Otimização de Performance
* **Problema:** A geração de embeddings com o provedor Ollama é atualmente sequencial, realizando uma chamada de API para cada chunk de texto. Para documentos grandes, isso resulta em alta latência e sobrecarga de rede.

#### Parte 1: Visão do Product Owner
* **História de Usuário:** Como um Engenheiro de Dados, eu quero que o sistema processe todos os chunks de um documento em uma única requisição para a API do Ollama, para reduzir drasticamente o tempo total de geração de embeddings e melhorar a eficiência do processo de ingestão.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Dado o upload de um documento que é dividido em 100 chunks, quando o provedor "Local (Ollama)" é selecionado, o sistema deve realizar apenas **uma** chamada para o endpoint `/api/embed` do Ollama, enviando todos os 100 chunks na mesma requisição.
    * **AC 2:** O tempo de processamento para a geração de embeddings com Ollama deve ser significativamente menor em comparação com a implementação anterior (sequencial).

#### Parte 2: Instruções Detalhadas (Visão do Engenheiro)
* **Otimização a ser Aplicada:** Processamento em lote (Batch Processing).
* **Referência da API:** A documentação do Ollama confirma que o endpoint `POST /api/embed` aceita um campo `"input"` que pode ser uma lista de strings (`["texto 1", "texto 2", ...]`).
* **Arquivo a ser Modificado:** `src/application/services/ingestion_service.py`
* **Instruções:**
    1.  Localize a função `_generate_embeddings_ollama`.
    2.  Remova o loop `for chunk in chunks:`.
    3.  Construa um único payload JSON onde a chave `"input"` contém a lista completa de `chunks`.
    4.  Realize uma única chamada `httpx.AsyncClient.post` com este payload.
    5.  A resposta da API conterá uma lista de `embeddings` na mesma ordem dos chunks enviados. Processe esta lista para retornar todos os vetores gerados.

---
### História 2: Otimizar Persistência no Neo4j com Inserção em Massa (Bulk Insert)

* **Tipo:** Otimização de Banco de Dados
* **Problema:** Os chunks e seus respectivos embeddings são salvos no Neo4j um por um, dentro de um loop. Isso causa o problema "N+1", gerando um grande número de transações e viagens de ida e volta (round-trips) para o banco de dados, o que é extremamente ineficiente.

#### Parte 1: Visão do Product Owner
* **História de Usuário:** Como o Sistema, eu preciso salvar todos os chunks de um documento no Neo4j em uma única transação, para minimizar a sobrecarga do banco de dados e acelerar a etapa de persistência dos dados.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Durante a ingestão de um documento com múltiplos chunks, deve ser executada apenas **uma** query Cypher para criar todos os nós `:Chunk` no Neo4j.
    * **AC 2:** O log da aplicação deve indicar que todos os chunks foram salvos em uma única transação.

#### Parte 2: Instruções Detalhadas (Visão do Engenheiro)
* **Otimização a ser Aplicada:** Inserção em massa usando a cláusula `UNWIND` do Cypher.
* **Arquivo a ser Modificado:** `src/application/services/ingestion_service.py`
* **Instruções:**
    1.  Localize a função `_save_to_neo4j`.
    2.  Antes da chamada ao banco de dados, crie uma lista de dicionários. Cada dicionário representará um chunk e conterá suas propriedades (`chunk_id`, `text`, `embedding`, `chunk_index`, etc.).
    3.  Remova o loop `for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):`.
    4.  Reescreva a query Cypher para usar `UNWIND`. A query receberá a lista de dicionários como um único parâmetro (ex: `$chunks_data`).
    5.  **Exemplo da nova query Cypher:**
        ```cypher
        UNWIND $chunks_data AS chunk
        CREATE (c:Chunk {
            id: chunk.chunk_id,
            text: chunk.text,
            embedding: chunk.embedding,
            source_file: $source_file,
            document_id: $document_id,
            chunk_index: chunk.chunk_index,
            created_at: datetime()
        })
        ```
    6.  Execute esta query uma única vez, passando a lista de dados dos chunks como parâmetro.

---
### História 3: Otimizar Custo e Armazenamento com Embeddings de Dimensão Reduzida (OpenAI)

* **Tipo:** Otimização de Custo e Recursos
* **Problema:** Estamos utilizando a dimensão padrão (1536) para o modelo `text-embedding-3-small` da OpenAI. Vetores grandes consomem mais espaço de armazenamento, aumentam os custos da API e tornam as buscas por similaridade mais lentas, sem necessariamente um ganho proporcional na qualidade para nosso caso de uso.

#### Parte 1: Visão do Product Owner
* **História de Usuário:** Como um Engenheiro de IA, eu quero configurar o sistema para gerar embeddings da OpenAI com uma dimensão menor, para reduzir os custos de armazenamento e API, e acelerar as buscas no banco de dados vetorial.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Quando eu configuro a dimensão do embedding da OpenAI para `256` e faço o upload de um documento, os vetores salvos no Neo4j devem ter exatamente 256 dimensões.
    * **AC 2:** O índice vetorial no Neo4j deve ser criado ou verificado para corresponder à dimensão configurada (256), garantindo que as buscas funcionem corretamente.

#### Parte 2: Instruções Detalhadas (Visão do Engenheiro)
* **Otimização a ser Aplicada:** Redução de dimensionalidade nativa da API.
* **Referência da API:** A documentação da OpenAI para os modelos `text-embedding-3` confirma a existência do parâmetro `dimensions` na chamada da API para controlar o tamanho do vetor de saída.
* **Arquivos a serem Modificados:** `src/config/settings.py` e `src/application/services/ingestion_service.py`.
* **Instruções:**
    1.  **Configuração:** Em `src/config/settings.py`, adicione uma nova variável de configuração, por exemplo, `OPENAI_EMBEDDING_DIMENSIONS: int = 256`.
    2.  **Geração de Embedding:** Em `ingestion_service.py`, na função `_generate_embeddings_openai`, adicione o par chave-valor `"dimensions": settings.OPENAI_EMBEDDING_DIMENSIONS` ao `json_payload` enviado para a API da OpenAI.
    3.  **Índice Vetorial (CRÍTICO):** Na função `_ensure_vector_index`, a dimensão do índice não pode ser fixada (`hardcoded`). Modifique a query de criação do índice para usar o valor da nova configuração.
        * **Exemplo da alteração na query:**
            ```cypher
            CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {
                indexConfig: {
                    `vector.dimensions`: ${settings.OPENAI_EMBEDDING_DIMENSIONS}, 
                    `vector.similarity_function`: 'cosine'
                }
            }
            ```
        * **Atenção:** Será necessário garantir que esta configuração seja consistente para todos os provedores ou criar uma lógica para gerenciar índices de diferentes dimensões se necessário no futuro. Para esta história, assumimos que a dimensão será a mesma para todos.
