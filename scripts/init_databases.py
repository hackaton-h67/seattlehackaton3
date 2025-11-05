#!/usr/bin/env python3
"""
Initialize databases for Service-Sense.

This script:
1. Creates Neo4j schema and indexes
2. Initializes ChromaDB collections
3. Creates PostgreSQL tables
4. Sets up initial data
"""

import asyncio
from neo4j import GraphDatabase
import chromadb
from sqlalchemy import create_engine, text

from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


def init_neo4j():
    """Initialize Neo4j database."""
    logger.info("initializing_neo4j")

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )

    with driver.session(database=settings.neo4j_database) as session:
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT service_code IF NOT EXISTS FOR (s:Service) REQUIRE s.code IS UNIQUE",
            "CREATE CONSTRAINT department_acronym IF NOT EXISTS FOR (d:Department) REQUIRE d.acronym IS UNIQUE",
            "CREATE CONSTRAINT neighborhood_name IF NOT EXISTS FOR (n:Neighborhood) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT request_number IF NOT EXISTS FOR (r:ServiceRequest) REQUIRE r.number IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                session.run(constraint)
                logger.info("created_constraint", query=constraint)
            except Exception as e:
                logger.warning("constraint_exists", error=str(e))

        # Create indexes
        indexes = [
            "CREATE INDEX service_name IF NOT EXISTS FOR (s:Service) ON (s.name)",
            "CREATE INDEX department_name IF NOT EXISTS FOR (d:Department) ON (d.full_name)",
            "CREATE INDEX request_status IF NOT EXISTS FOR (r:ServiceRequest) ON (r.status)",
            "CREATE INDEX request_date IF NOT EXISTS FOR (r:ServiceRequest) ON (r.created_date)",
        ]

        for index in indexes:
            try:
                session.run(index)
                logger.info("created_index", query=index)
            except Exception as e:
                logger.warning("index_exists", error=str(e))

    driver.close()
    logger.info("neo4j_initialized")


def init_chromadb():
    """Initialize ChromaDB collections."""
    logger.info("initializing_chromadb")

    client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port
    )

    # Create collection for service requests
    try:
        collection = client.create_collection(
            name=settings.chroma_collection,
            metadata={"description": "Historical service requests for similarity search"}
        )
        logger.info("created_chroma_collection", name=settings.chroma_collection)
    except Exception as e:
        logger.warning("collection_exists", error=str(e))

    logger.info("chromadb_initialized")


def init_postgres():
    """Initialize PostgreSQL database."""
    logger.info("initializing_postgres")

    engine = create_engine(settings.postgres_url)

    with engine.connect() as conn:
        # Create tables
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                request_number VARCHAR(50),
                request_id UUID,
                actual_resolution_days INTEGER,
                user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
                comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                request_id UUID UNIQUE,
                service_code VARCHAR(100),
                predicted_days FLOAT,
                confidence_lower FLOAT,
                confidence_upper FLOAT,
                model_version VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ab_experiments (
                id SERIAL PRIMARY KEY,
                experiment_name VARCHAR(100),
                variant VARCHAR(50),
                user_id VARCHAR(100),
                metric_name VARCHAR(100),
                metric_value FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.commit()
        logger.info("created_postgres_tables")

    logger.info("postgres_initialized")


def main():
    """Initialize all databases."""
    logger.info("starting_database_initialization")

    try:
        init_neo4j()
        init_chromadb()
        init_postgres()
        logger.info("database_initialization_complete")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
