### História 1: Criar Script de Limpeza e Reset do Banco de Dados

* **Tipo:** Ferramenta de Desenvolvimento
* **Problema:** Durante o desenvolvimento e testes, é necessário resetar frequentemente o estado do banco de dados para garantir um ambiente limpo. Fazer isso manualmente é demorado e propenso a erros.

#### Parte 1: Visão do Product Owner
* **História de Usuário:** Como um Desenvolvedor, eu preciso de um script de linha de comando para apagar completamente todos os dados do banco de dados Neo4j, para que eu possa resetar o estado do sistema de forma rápida e confiável.
* **Critérios de Aceite (ACs):**
    * **AC 1:** Ao executar o script `scripts/clear_database.py`, ele deve primeiro solicitar uma confirmação explícita do usuário para evitar a exclusão acidental de dados.
    * **AC 2:** Se a exclusão for confirmada, o script deve apagar todos os nós `:Chunk` e remover o índice vetorial `document_embeddings` do Neo4j.
    * **AC 3:** Após a execução bem-sucedida do script, o banco de dados deve estar completamente vazio, e um novo upload de documento deve funcionar corretamente, recriando o índice e os nós.

#### Parte 2: Instruções Detalhadas (Visão do Engenheiro)
* **Otimização a ser Aplicada:** Melhoria da Experiência do Desenvolvedor (DX) e Automatização de Tarefas de Teste.
* **Arquivo a ser Criado:** `scripts/clear_database.py`
* **Instruções:**
    1.  Crie o novo arquivo de script na pasta `scripts`.
    2.  No script, utilize o driver do `neo4j` para se conectar ao banco de dados, reutilizando as configurações de conexão do `settings`.
    3.  Implemente um prompt de confirmação que exija que o usuário digite "sim" ou "yes" para prosseguir. Se qualquer outra coisa for inserida, o script deve ser encerrado.
    4.  Se confirmado, execute as seguintes queries Cypher em uma sessão do Neo4j:
        * Primeiro, a query para apagar o índice: `DROP INDEX document_embeddings IF EXISTS`
        * Segundo, a query para apagar todos os chunks: `MATCH (n:Chunk) DETACH DELETE n`
    5.  Imprima mensagens de status claras no console (ex: "Conectando ao banco de dados...", "Índice 'document_embeddings' removido.", "Todos os nós :Chunk foram removidos.", "Banco de dados limpo com sucesso.").
    6.  Garanta que a conexão com o banco de dados seja fechada corretamente no final da execução, mesmo em caso de erro.
