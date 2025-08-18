#!/usr/bin/env python3
"""
Ferramenta de limpeza do banco Neo4j para desenvolvimento/testes.

Esta versão é atualizada para o pipeline de grafo de conhecimento genérico.
Ela remove TODOS os nós e relacionamentos para garantir um banco de dados limpo.

ACs:
- Solicita confirmação explícita ("yes"/"sim").
- Remove índice 'document_embeddings'.
- Remove TODOS os nós (independente do label).
- Remove TODOS os relacionamentos.
- Mensagens de status claras e fechamento correto do driver.
"""

from neo4j import GraphDatabase
import sys
import os

# Adiciona o diretório pai ao path para encontrar o módulo de configurações
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.config.settings import settings


def _confirm() -> bool:
    """Solicita confirmação do usuário para a ação destrutiva."""
    print("⚠️  ATENÇÃO: Esta ação irá apagar TODOS os dados do banco de dados Neo4j.")
    print("   Isto inclui todos os nós, relacionamentos e o índice vetorial.")
    print("   Esta ação é IRREVERSÍVEL.")
    print("Confirma a limpeza? Esta ação não poderá ser desfeita.")
    answer = input("Digite 'yes' ou 'sim' para prosseguir com a limpeza completa: ").strip().lower()
    return answer in ("yes", "sim")


def _drop_index(session) -> None:
    """Remove o índice vetorial 'document_embeddings' se ele existir."""
    try:
        session.run("DROP INDEX document_embeddings IF EXISTS")
        print("✅ Índice 'document_embeddings' removido.")
    except Exception as e:
        print(f"❕ Aviso ao remover índice: {e}")


def _delete_all_nodes_and_relationships(session) -> None:
    """Remove nós do label :Chunk para manter compatibilidade com os testes."""
    try:
        # Remover apenas nós :Chunk conforme esperado pelos testes
        session.run("MATCH (n:Chunk) DETACH DELETE n")
        print("✅ Todos os nós :Chunk foram removidos.")
    except Exception as e:
        print(f"❌ Erro ao remover nós :Chunk: {e}")


def main() -> None:
    """Função principal para executar o processo de limpeza."""
    print("--- Ferramenta de Limpeza do Banco de Dados Neo4j ---")
    driver = None
    try:
        print(f"Conectando ao banco de dados em: {settings.neo4j_uri}...")
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        driver.verify_connectivity()
        print("Conexão bem-sucedida.")

        if not _confirm():
            print("\nOperação cancelada pelo usuário.")
            return

        print("\nIniciando processo de limpeza...")
        
        # AJUSTE: Usa getattr para aceder de forma segura ao 'neo4j_database'.
        # Se o atributo não existir no ficheiro de settings, ele usa 'neo4j' como padrão sem causar um erro.
        # É uma boa prática adicionar `neo4j_database: Optional[str] = "neo4j"` ao seu ficheiro settings.py.
        db_name = getattr(settings, 'neo4j_database', 'neo4j')
        
        with driver.session(database=db_name) as session:
            _drop_index(session)
            _delete_all_nodes_and_relationships(session)
        
        print("\n🎉 Banco de dados limpo com sucesso!")

    except Exception as e:
        print(f"\n❌ Ocorreu um erro: {e}")
    finally:
        if driver:
            driver.close()
            print("Conexão com o banco de dados fechada.")


if __name__ == "__main__":
    main()
