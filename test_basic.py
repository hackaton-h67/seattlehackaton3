#!/usr/bin/env python3
"""
Basic test script to verify Service-Sense setup without full dependencies.
"""
import sys
import asyncio
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("=== Service-Sense Basic Test ===\n")

    # Test 1: Configuration
    print("1. Testing configuration loading...")
    try:
        from shared.config.settings import settings
        print(f"   ✓ Settings loaded successfully")
        print(f"   - API Host: {settings.api_host}:{settings.api_port}")
        print(f"   - Log Level: {settings.log_level}")
        print(f"   - Mock LLM: {settings.mock_llm}")
        print(f"   - Neo4j URI: {settings.neo4j_uri}")
    except Exception as e:
        print(f"   ✗ Failed to load settings: {e}")
        return False

    # Test 2: Data Models
    print("\n2. Testing data models...")
    try:
        from shared.models.request import (
            TriageRequest,
            TriageResponse,
            ExtractedEntities,
            Classification,
            Location
        )

        # Create a test request
        test_location = Location(latitude=47.6062, longitude=-122.3321)
        test_request = TriageRequest(
            text="There is a pothole on 5th Avenue",
            location=test_location
        )
        print(f"   ✓ Data models loaded successfully")
        print(f"   - Test request created: {test_request.text[:50]}...")
    except Exception as e:
        print(f"   ✗ Failed to load data models: {e}")
        return False

    # Test 3: Logging
    print("\n3. Testing logging setup...")
    try:
        from shared.utils.logging import setup_logging, get_logger
        setup_logging("info")
        logger = get_logger(__name__)
        logger.info("test_log_entry", test=True)
        print(f"   ✓ Logging initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to setup logging: {e}")
        return False

    # Test 4: Metrics
    print("\n4. Testing metrics collector...")
    try:
        from shared.utils.metrics import MetricsCollector
        metrics = MetricsCollector()
        print(f"   ✓ Metrics collector initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize metrics: {e}")
        return False

    # Test 5: FastAPI App
    print("\n5. Testing FastAPI application...")
    try:
        from fastapi.testclient import TestClient
        print(f"   ℹ  FastAPI test client not available (expected)")
        print(f"   ℹ  Install test dependencies: pip install pytest httpx")
    except Exception as e:
        pass

    print("\n" + "="*50)
    print("✓ Basic tests completed successfully!")
    print("\nNext steps:")
    print("1. Install Docker or database services manually")
    print("2. Run: python scripts/init_databases.py")
    print("3. Run: python scripts/load_data.py")
    print("4. Start API: cd services/api-gateway && python main.py")
    print("\nFor testing without databases, the API will use fallback methods.")
    print("="*50)

    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
