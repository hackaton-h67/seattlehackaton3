"""
Vector Search Service - Semantic similarity search using ChromaDB.
"""

from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from shared.models.request import ExtractedEntities
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class VectorSearchService:
    """ChromaDB-based vector similarity search."""

    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_model = None

        if settings.enable_vector_search:
            try:
                # Initialize ChromaDB client
                self.client = chromadb.HttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                    settings=ChromaSettings(
                        anonymized_telemetry=False
                    )
                )

                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name=settings.chroma_collection,
                    metadata={"description": "Seattle service requests"}
                )

                # Initialize embedding model
                self.embedding_model = SentenceTransformer(settings.embedding_model)

                logger.info(
                    "vector_search_initialized",
                    collection=settings.chroma_collection,
                    model=settings.embedding_model
                )
            except Exception as e:
                logger.error("vector_search_init_failed", error=str(e))
                logger.warning("vector_search_disabled")
        else:
            logger.warning("vector_search_disabled_by_config")

    async def search_similar_requests(
        self,
        query_text: str,
        entities: ExtractedEntities,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar historical requests.

        Args:
            query_text: User's request text
            entities: Extracted entities
            limit: Number of results to return

        Returns:
            List of similar requests with metadata
        """
        if not self.collection or not self.embedding_model:
            logger.warning("vector_search_not_available")
            return []

        try:
            # Enhance query with entity keywords
            enhanced_query = self._enhance_query(query_text, entities)

            # Generate embedding
            query_embedding = self.embedding_model.encode([enhanced_query])[0].tolist()

            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            similar_requests = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    similar_requests.append({
                        "request_number": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "resolution_days": results["metadatas"][0][i].get("resolution_days"),
                        "service_type": results["metadatas"][0][i].get("service_type"),
                        "department": results["metadatas"][0][i].get("department")
                    })

            logger.info(
                "vector_search_complete",
                query_length=len(query_text),
                results_found=len(similar_requests)
            )

            return similar_requests

        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []

    def _enhance_query(self, text: str, entities: ExtractedEntities) -> str:
        """Enhance query with extracted keywords for better matching."""
        enhanced = text

        if entities.service_keywords:
            enhanced += " " + " ".join(entities.service_keywords)

        if entities.location and entities.location.address:
            enhanced += f" location: {entities.location.address}"

        if entities.urgency_indicators:
            enhanced += " urgent"

        return enhanced

    async def add_request(
        self,
        request_number: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a service request to the vector database.

        Args:
            request_number: Unique request ID
            text: Request text to embed
            metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.collection or not self.embedding_model:
            return False

        try:
            # Generate embedding
            embedding = self.embedding_model.encode([text])[0].tolist()

            # Add to collection
            self.collection.add(
                ids=[request_number],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )

            logger.info("request_added_to_vector_db", request_number=request_number)
            return True

        except Exception as e:
            logger.error("add_request_failed", request_number=request_number, error=str(e))
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection."""
        if not self.collection:
            return {"status": "unavailable"}

        try:
            count = self.collection.count()
            return {
                "status": "active",
                "collection_name": settings.chroma_collection,
                "total_requests": count,
                "embedding_dimension": settings.embedding_dimension
            }
        except Exception as e:
            logger.error("stats_failed", error=str(e))
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import asyncio

    async def test():
        service = VectorSearchService()

        # Test adding a request
        await service.add_request(
            request_number="TEST-001",
            text="Large pothole on 5th Avenue causing car damage",
            metadata={
                "service_type": "SDOT_POTHOLE",
                "department": "SDOT",
                "resolution_days": 7
            }
        )

        # Test search
        from shared.models.request import ExtractedEntities
        entities = ExtractedEntities(service_keywords=["pothole"])

        results = await service.search_similar_requests(
            "There is a big hole in the street",
            entities,
            limit=3
        )

        print(f"\nFound {len(results)} similar requests:")
        for r in results:
            print(f"  - {r['request_number']}: {r['text'][:50]}... (similarity: {r['similarity_score']:.2f})")

        # Stats
        stats = await service.get_collection_stats()
        print(f"\nCollection stats: {stats}")

    asyncio.run(test())
