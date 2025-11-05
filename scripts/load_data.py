#!/usr/bin/env python3
"""
Load Seattle Open Data into Service-Sense databases.

This script fetches data from Seattle's Open Data API and loads it into:
1. Neo4j (graph relationships)
2. ChromaDB (vector embeddings)
3. PostgreSQL (application data)
"""

import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any

from shared.config.settings import settings
from shared.utils.logging import setup_logging, get_logger

setup_logging("INFO")
logger = get_logger(__name__)


async def fetch_seattle_data(limit: int = 10000, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Fetch data from Seattle Open Data API.

    Args:
        limit: Number of records to fetch
        offset: Offset for pagination

    Returns:
        List of service request records
    """
    url = settings.seattle_data_api
    params = {
        "$limit": limit,
        "$offset": offset,
        "$order": "createddate DESC"
    }

    if settings.seattle_data_app_token:
        headers = {"X-App-Token": settings.seattle_data_app_token}
    else:
        headers = {}

    logger.info("fetching_seattle_data", limit=limit, offset=offset)

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    logger.info("fetched_records", count=len(data))
    return data


def transform_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Seattle Open Data record to our schema.

    Args:
        record: Raw record from API

    Returns:
        Transformed record
    """
    return {
        "number": record.get("servicerequestnumber"),
        "service_type": record.get("webintakeservicerequests"),
        "department": record.get("departmentname"),
        "created_date": record.get("createddate"),
        "status": record.get("servicerequeststatusname"),
        "method_received": record.get("methodreceivedname"),
        "location": record.get("location"),
        "latitude": float(record["latitude"]) if record.get("latitude") else None,
        "longitude": float(record["longitude"]) if record.get("longitude") else None,
        "zipcode": record.get("zipcode"),
        "council_district": record.get("councildistrict"),
        "neighborhood": record.get("neighborhood"),
        "police_precinct": record.get("policeprecinct"),
    }


async def load_to_neo4j(records: List[Dict[str, Any]]):
    """Load records into Neo4j."""
    logger.info("loading_to_neo4j", count=len(records))
    # TODO: Implement Neo4j loading
    # 1. Create Service nodes
    # 2. Create Department nodes
    # 3. Create ServiceRequest nodes
    # 4. Create relationships
    pass


async def load_to_chromadb(records: List[Dict[str, Any]]):
    """Load records into ChromaDB with embeddings."""
    logger.info("loading_to_chromadb", count=len(records))
    # TODO: Implement ChromaDB loading
    # 1. Generate embeddings for request text
    # 2. Store in ChromaDB with metadata
    pass


async def main():
    """Main data loading pipeline."""
    logger.info("starting_data_load")

    # Fetch data in batches
    batch_size = 1000
    total_loaded = 0

    for offset in range(0, 10000, batch_size):
        records = await fetch_seattle_data(limit=batch_size, offset=offset)

        if not records:
            break

        # Transform records
        transformed = [transform_record(r) for r in records]

        # Load to databases
        await load_to_neo4j(transformed)
        await load_to_chromadb(transformed)

        total_loaded += len(records)
        logger.info("batch_loaded", total=total_loaded)

    logger.info("data_load_complete", total_records=total_loaded)


if __name__ == "__main__":
    asyncio.run(main())
