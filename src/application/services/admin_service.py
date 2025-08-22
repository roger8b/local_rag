"""
Service for database administration tasks.
"""
from neo4j import GraphDatabase
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseAdminService:
    """
    Service for handling database administration tasks like clearing the database.
    """
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            self.driver.verify_connectivity()
            self._db_disabled = False
            logger.info("DatabaseAdminService: Neo4j connection established.")
        except Exception as e:
            logger.error(f"DatabaseAdminService: Neo4j connection failed: {e}")
            self.driver = None
            self._db_disabled = True

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("DatabaseAdminService: Neo4j connection closed.")

    def clear_database(self):
        """Drops all indexes and deletes all nodes and relationships from the database."""
        if self._db_disabled:
            raise ConnectionError("Database is not available.")

        queries = [
            "DROP INDEX document_embeddings IF EXISTS",
            "MATCH (n) DETACH DELETE n"
        ]

        try:
            with self.driver.session() as session:
                for query in queries:
                    logger.info(f"Executing query: {query}")
                    session.run(query)
            logger.info("Database cleared successfully.")
            return {"status": "success", "message": "Database cleared successfully."}
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            raise
