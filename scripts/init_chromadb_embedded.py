#!/usr/bin/env python3
"""
Initialize ChromaDB in embedded mode (no server required).

This allows us to set up ChromaDB locally without Docker or a ChromaDB server.
"""

import chromadb
from pathlib import Path

from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


def init_chromadb_embedded():
    """Initialize ChromaDB in embedded mode."""
    logger.info("initializing_chromadb_embedded")

    # Create data directory
    data_dir = Path("./data/chroma")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize embedded client
    client = chromadb.PersistentClient(path=str(data_dir))

    # Create collection for service requests
    try:
        collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"description": "Historical service requests for similarity search"}
        )
        logger.info("created_chroma_collection",
                   name=settings.chroma_collection,
                   count=collection.count())
    except Exception as e:
        logger.error("failed_to_create_collection", error=str(e))
        raise

    logger.info("chromadb_initialized_embedded", path=str(data_dir))
    return client, collection


def main():
    """Initialize ChromaDB."""
    logger.info("starting_chromadb_initialization")

    try:
        client, collection = init_chromadb_embedded()
        logger.info("chromadb_initialization_complete",
                   collection=settings.chroma_collection,
                   records=collection.count())
        print(f"\n✅ ChromaDB initialized successfully!")
        print(f"   Collection: {settings.chroma_collection}")
        print(f"   Records: {collection.count()}")
        print(f"   Data directory: ./data/chroma")
    except Exception as e:
        logger.error("chromadb_initialization_failed", error=str(e))
        print(f"\n❌ ChromaDB initialization failed: {e}")
        raise


if __name__ == "__main__":
    main()
