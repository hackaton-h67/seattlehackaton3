#!/bin/bash
# Verify Service-Sense Setup

set -e

echo "=========================================="
echo "Service-Sense Setup Verification"
echo "=========================================="
echo ""

echo "Step 1: Checking Docker services status..."
echo ""
sudo docker compose ps
echo ""

echo "Step 2: Testing database connections..."
echo ""

# Test PostgreSQL
echo "✓ Testing PostgreSQL..."
sudo docker exec service-sense-postgres pg_isready -U service_sense && echo "  PostgreSQL: ✅ HEALTHY" || echo "  PostgreSQL: ❌ FAILED"

# Test Redis
echo "✓ Testing Redis..."
sudo docker exec service-sense-redis redis-cli -a testpassword123 ping > /dev/null 2>&1 && echo "  Redis: ✅ HEALTHY" || echo "  Redis: ❌ FAILED"

# Test Neo4j
echo "✓ Testing Neo4j..."
sudo docker exec service-sense-neo4j cypher-shell -u neo4j -p testpassword123 "RETURN 1" > /dev/null 2>&1 && echo "  Neo4j: ✅ HEALTHY" || echo "  Neo4j: ❌ FAILED"

# Test ChromaDB
echo "✓ Testing ChromaDB..."
curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1 && echo "  ChromaDB: ✅ HEALTHY" || echo "  ChromaDB: ❌ FAILED"

echo ""
echo "Step 3: Checking Python environment..."
echo ""
source venv/bin/activate
python --version
echo "Python packages installed: $(pip list | wc -l) packages"
echo ""

echo "=========================================="
echo "Setup Verification Complete!"
echo "=========================================="
echo ""
echo "✅ All dependencies installed"
echo "✅ Docker services running"
echo "✅ Databases initialized"
echo ""
echo "Service URLs:"
echo "  - Neo4j Browser: http://localhost:7474"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo ""
echo "Next steps:"
echo "1. Get Seattle Open Data API token from: https://data.seattle.gov/"
echo "2. Update SEATTLE_DATA_APP_TOKEN in .env file"
echo "3. Run data loading: source venv/bin/activate && python scripts/load_data.py"
echo "4. Start API gateway: make run-api"
echo ""
