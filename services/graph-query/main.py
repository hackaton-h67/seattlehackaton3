"""
Graph Query Service - Query Neo4j knowledge graph for relationships.
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from shared.models.request import ExtractedEntities
from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging(settings.log_level)
logger = get_logger(__name__)


class GraphQueryService:
    """Neo4j graph database queries for service relationships."""

    def __init__(self):
        self.driver = None

        if settings.enable_graph_search:
            try:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                    max_connection_pool_size=settings.neo4j_max_connections
                )

                # Test connection
                with self.driver.session(database=settings.neo4j_database) as session:
                    session.run("RETURN 1")

                logger.info("graph_query_initialized", uri=settings.neo4j_uri)
            except ServiceUnavailable as e:
                logger.error("neo4j_unavailable", error=str(e))
                self.driver = None
            except Exception as e:
                logger.error("graph_query_init_failed", error=str(e))
                self.driver = None
        else:
            logger.warning("graph_search_disabled_by_config")

    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()

    async def find_services_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find services matching keywords.

        Args:
            keywords: List of service keywords
            limit: Maximum number of results

        Returns:
            List of matching services
        """
        if not self.driver or not keywords:
            return []

        try:
            query = """
            MATCH (s:Service)-[:HAS_KEYWORD]->(k:Keyword)
            WHERE k.text IN $keywords
            WITH s, count(k) as keyword_matches
            MATCH (s)-[:HANDLED_BY]->(d:Department)
            RETURN s.code as service_code,
                   s.name as service_name,
                   s.description as description,
                   d.acronym as department,
                   s.priority as priority,
                   s.sla_days as sla_days,
                   keyword_matches
            ORDER BY keyword_matches DESC, s.priority ASC
            LIMIT $limit
            """

            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run(query, keywords=keywords, limit=limit)
                services = [dict(record) for record in result]

            logger.info("services_found_by_keywords", count=len(services), keywords=keywords)
            return services

        except Exception as e:
            logger.error("find_services_failed", error=str(e))
            return []

    async def get_neighborhood_patterns(
        self,
        neighborhood: str,
        service_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical patterns for a neighborhood.

        Args:
            neighborhood: Neighborhood name
            service_code: Optional service code filter

        Returns:
            Pattern statistics
        """
        if not self.driver or not neighborhood:
            return {}

        try:
            if service_code:
                query = """
                MATCH (n:Neighborhood {name: $neighborhood})<-[:LOCATED_IN]-(r:ServiceRequest)-[:FILED_FOR]->(s:Service {code: $service_code})
                WHERE r.resolution_days IS NOT NULL
                RETURN s.code as service_code,
                       s.name as service_name,
                       count(r) as request_count,
                       avg(r.resolution_days) as avg_resolution_days,
                       percentileCont(r.resolution_days, 0.5) as median_resolution_days,
                       min(r.resolution_days) as min_resolution_days,
                       max(r.resolution_days) as max_resolution_days
                """
                params = {"neighborhood": neighborhood.upper(), "service_code": service_code}
            else:
                query = """
                MATCH (n:Neighborhood {name: $neighborhood})<-[:LOCATED_IN]-(r:ServiceRequest)-[:FILED_FOR]->(s:Service)
                WHERE r.resolution_days IS NOT NULL
                WITH s, count(r) as request_count, avg(r.resolution_days) as avg_days
                RETURN s.code as service_code,
                       s.name as service_name,
                       request_count,
                       avg_days as avg_resolution_days
                ORDER BY request_count DESC
                LIMIT 10
                """
                params = {"neighborhood": neighborhood.upper()}

            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run(query, **params)
                patterns = [dict(record) for record in result]

            logger.info(
                "neighborhood_patterns_retrieved",
                neighborhood=neighborhood,
                patterns_count=len(patterns)
            )

            return {
                "neighborhood": neighborhood,
                "patterns": patterns
            }

        except Exception as e:
            logger.error("get_neighborhood_patterns_failed", error=str(e))
            return {}

    async def get_department_workload(self) -> List[Dict[str, Any]]:
        """
        Get current workload by department.

        Returns:
            List of departments with request counts
        """
        if not self.driver:
            return []

        try:
            query = """
            MATCH (d:Department)<-[:RESOLVED_BY]-(r:ServiceRequest)
            WHERE r.status = 'Open'
            RETURN d.acronym as department,
                   d.full_name as department_name,
                   count(r) as open_requests
            ORDER BY open_requests DESC
            """

            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run(query)
                workload = [dict(record) for record in result]

            logger.info("department_workload_retrieved", departments=len(workload))
            return workload

        except Exception as e:
            logger.error("get_department_workload_failed", error=str(e))
            return []

    async def get_service_details(self, service_code: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a service.

        Args:
            service_code: Service code

        Returns:
            Service details with relationships
        """
        if not self.driver:
            return None

        try:
            query = """
            MATCH (s:Service {code: $service_code})
            OPTIONAL MATCH (s)-[:HANDLED_BY]->(d:Department)
            OPTIONAL MATCH (s)-[:HAS_KEYWORD]->(k:Keyword)
            OPTIONAL MATCH (s)-[:COMMON_IN]->(n:Neighborhood)
            RETURN s.code as code,
                   s.name as name,
                   s.description as description,
                   s.priority as priority,
                   s.sla_days as sla_days,
                   s.requires_photo as requires_photo,
                   s.requires_exact_location as requires_exact_location,
                   d.acronym as department,
                   d.full_name as department_name,
                   collect(DISTINCT k.text) as keywords,
                   collect(DISTINCT n.name) as common_neighborhoods
            """

            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run(query, service_code=service_code)
                record = result.single()

                if record:
                    service_details = dict(record)
                    logger.info("service_details_retrieved", service_code=service_code)
                    return service_details

            logger.warning("service_not_found", service_code=service_code)
            return None

        except Exception as e:
            logger.error("get_service_details_failed", error=str(e))
            return None

    async def find_similar_requests_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find requests near a location using spatial queries.

        Args:
            latitude: Latitude
            longitude: Longitude
            radius_km: Search radius in kilometers
            limit: Maximum results

        Returns:
            List of nearby requests
        """
        if not self.driver:
            return []

        try:
            # Note: This requires spatial index on ServiceRequest nodes
            query = """
            CALL spatial.withinDistance('service-requests', {latitude: $lat, longitude: $lon}, $radius)
            YIELD node as r
            MATCH (r)-[:FILED_FOR]->(s:Service)
            WHERE r.resolution_days IS NOT NULL
            RETURN r.number as request_number,
                   s.code as service_code,
                   s.name as service_name,
                   r.resolution_days as resolution_days,
                   r.created_date as created_date,
                   distance(point({latitude: $lat, longitude: $lon}),
                           point({latitude: r.latitude, longitude: r.longitude})) as distance_m
            ORDER BY distance_m ASC
            LIMIT $limit
            """

            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run(
                    query,
                    lat=latitude,
                    lon=longitude,
                    radius=radius_km * 1000,  # Convert to meters
                    limit=limit
                )
                nearby_requests = [dict(record) for record in result]

            logger.info("nearby_requests_found", count=len(nearby_requests))
            return nearby_requests

        except Exception as e:
            logger.error("find_nearby_requests_failed", error=str(e))
            return []


if __name__ == "__main__":
    import asyncio

    async def test():
        service = GraphQueryService()

        # Test keyword search
        services = await service.find_services_by_keywords(["pothole", "road"], limit=3)
        print(f"\nServices matching ['pothole', 'road']:")
        for s in services:
            print(f"  - {s.get('service_code')}: {s.get('service_name')} ({s.get('department')})")

        # Test department workload
        workload = await service.get_department_workload()
        print(f"\nDepartment workload:")
        for w in workload[:3]:
            print(f"  - {w.get('department')}: {w.get('open_requests')} open requests")

        service.close()

    asyncio.run(test())
