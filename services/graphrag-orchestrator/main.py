"""
GraphRAG Orchestrator - Combines vector and graph search for hybrid retrieval.
"""

import asyncio
from typing import Dict, Any, List
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'vector-search'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'graph-query'))

from shared.models.request import ExtractedEntities
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class GraphRAGOrchestrator:
    """Orchestrates hybrid retrieval from vector and graph databases."""

    def __init__(self):
        # Import services
        try:
            from services.vector_search.main import VectorSearchService
            from services.graph_query.main import GraphQueryService

            self.vector_search = VectorSearchService()
            self.graph_query = GraphQueryService()
            logger.info("graphrag_orchestrator_initialized")
        except ImportError:
            # Fallback for when running standalone
            self.vector_search = None
            self.graph_query = None
            logger.warning("services_not_available_running_in_standalone_mode")

    async def retrieve_context(
        self,
        user_input: str,
        entities: ExtractedEntities
    ) -> Dict[str, Any]:
        """
        Retrieve context from both vector and graph databases.

        Args:
            user_input: Original user input text
            entities: Extracted entities

        Returns:
            Unified context combining vector and graph results
        """
        logger.info("retrieving_hybrid_context")

        # Run searches in parallel
        vector_task = self._vector_retrieval(user_input, entities)
        graph_task = self._graph_retrieval(entities)

        vector_results, graph_results = await asyncio.gather(
            vector_task,
            graph_task,
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(vector_results, Exception):
            logger.error("vector_retrieval_failed", error=str(vector_results))
            vector_results = {"similar_requests": []}

        if isinstance(graph_results, Exception):
            logger.error("graph_retrieval_failed", error=str(graph_results))
            graph_results = {"services": [], "patterns": {}}

        # Merge results
        unified_context = self._merge_contexts(vector_results, graph_results)

        logger.info(
            "context_retrieved",
            similar_requests=len(unified_context.get("similar_requests", [])),
            matching_services=len(unified_context.get("matching_services", []))
        )

        return unified_context

    async def _vector_retrieval(
        self,
        user_input: str,
        entities: ExtractedEntities
    ) -> Dict[str, Any]:
        """Retrieve similar requests using vector search."""
        if not self.vector_search:
            return {"similar_requests": []}

        similar_requests = await self.vector_search.search_similar_requests(
            user_input,
            entities,
            limit=5
        )

        return {"similar_requests": similar_requests}

    async def _graph_retrieval(
        self,
        entities: ExtractedEntities
    ) -> Dict[str, Any]:
        """Retrieve relationships and patterns using graph queries."""
        if not self.graph_query:
            return {"services": [], "patterns": {}}

        results = {}

        # Find services by keywords
        if entities.service_keywords:
            services = await self.graph_query.find_services_by_keywords(
                entities.service_keywords,
                limit=5
            )
            results["services"] = services
        else:
            results["services"] = []

        # Get neighborhood patterns if location available
        if entities.location and entities.location.neighborhood:
            patterns = await self.graph_query.get_neighborhood_patterns(
                entities.location.neighborhood
            )
            results["patterns"] = patterns
        else:
            results["patterns"] = {}

        return results

    def _merge_contexts(
        self,
        vector_results: Dict[str, Any],
        graph_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Intelligently merge vector and graph results.

        Deduplication and relevance weighting:
        - Similar requests provide specific examples
        - Graph services provide domain knowledge
        - Neighborhood patterns provide local context
        """
        unified = {
            "similar_requests": vector_results.get("similar_requests", []),
            "matching_services": graph_results.get("services", []),
            "neighborhood_patterns": graph_results.get("patterns", {}),
            "data_sources": []
        }

        # Track which sources contributed
        if unified["similar_requests"]:
            unified["data_sources"].append("vector_similarity")

        if unified["matching_services"]:
            unified["data_sources"].append("graph_relationships")

        if unified["neighborhood_patterns"]:
            unified["data_sources"].append("neighborhood_history")

        return unified

    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """
        Format the unified context for LLM consumption.

        Args:
            context: Unified context from retrieve_context()

        Returns:
            Formatted string for LLM prompt
        """
        sections = []

        # Similar requests section
        if context.get("similar_requests"):
            sections.append("### Similar Historical Requests:")
            for i, req in enumerate(context["similar_requests"][:3], 1):
                similarity = req.get("similarity_score", 0)
                service_type = req.get("service_type", "Unknown")
                resolution_days = req.get("resolution_days", "N/A")
                sections.append(
                    f"{i}. {req.get('text', '')[:100]}...\n"
                    f"   Service: {service_type}, Resolution Time: {resolution_days} days, "
                    f"Similarity: {similarity:.2f}"
                )

        # Matching services section
        if context.get("matching_services"):
            sections.append("\n### Matching Service Types:")
            for i, svc in enumerate(context["matching_services"][:3], 1):
                sections.append(
                    f"{i}. {svc.get('service_name')} ({svc.get('service_code')})\n"
                    f"   Department: {svc.get('department')}, "
                    f"SLA: {svc.get('sla_days', 'N/A')} days, "
                    f"Priority: {svc.get('priority', 'N/A')}"
                )

        # Neighborhood patterns section
        if context.get("neighborhood_patterns") and context["neighborhood_patterns"].get("patterns"):
            patterns = context["neighborhood_patterns"]
            sections.append(f"\n### {patterns.get('neighborhood')} Neighborhood Patterns:")
            for pattern in patterns["patterns"][:3]:
                sections.append(
                    f"- {pattern.get('service_name')}: "
                    f"avg {pattern.get('avg_resolution_days', 0):.1f} days "
                    f"({pattern.get('request_count', 0)} requests)"
                )

        if not sections:
            return "No additional context available from historical data."

        return "\n".join(sections)


if __name__ == "__main__":
    async def test():
        orchestrator = GraphRAGOrchestrator()

        from shared.models.request import ExtractedEntities

        # Test case
        entities = ExtractedEntities(
            service_keywords=["pothole", "road"],
            location=None
        )

        context = await orchestrator.retrieve_context(
            "There's a pothole on the street",
            entities
        )

        print("\nRetrieved Context:")
        print(f"Similar requests: {len(context.get('similar_requests', []))}")
        print(f"Matching services: {len(context.get('matching_services', []))}")
        print(f"Data sources: {context.get('data_sources', [])}")

        print("\n\nFormatted for LLM:")
        formatted = orchestrator.format_context_for_llm(context)
        print(formatted)

    asyncio.run(test())
