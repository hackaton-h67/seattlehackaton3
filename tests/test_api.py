"""
Basic API tests for Service-Sense.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "api-gateway"))

from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Service-Sense API"
    assert data["version"] == "2.0.0"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_triage_text_request():
    """Test triage endpoint with text input."""
    request_data = {
        "text": "There is a pothole on 5th Avenue and Pine Street",
        "location": {
            "latitude": 47.6115,
            "longitude": -122.3344
        }
    }

    response = client.post("/api/v2/triage", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "classification" in data
    assert "prediction" in data
    assert "reasoning" in data


def test_list_services():
    """Test services listing endpoint."""
    response = client.get("/api/v2/services")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
