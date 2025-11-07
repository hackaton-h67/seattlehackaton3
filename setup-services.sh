#!/bin/bash
# Service-Sense Setup Script
# This script will start all database services and initialize them

set -e

echo "=========================================="
echo "Service-Sense Database Setup"
echo "=========================================="
echo ""

# Start database services
echo "Step 1: Starting database services (PostgreSQL, Neo4j, ChromaDB, Redis)..."
sudo docker compose up -d postgres neo4j chromadb redis

echo ""
echo "Step 2: Waiting for services to become healthy (this may take 30-60 seconds)..."
sleep 10

# Check service status
echo ""
echo "Step 3: Checking service status..."
sudo docker compose ps

echo ""
echo "Step 4: Waiting for Neo4j to fully initialize..."
sleep 20

echo ""
echo "=========================================="
echo "Database Services Started Successfully!"
echo "=========================================="
echo ""
echo "Services running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Neo4j: localhost:7474 (browser) / localhost:7687 (bolt)"
echo "  - ChromaDB: localhost:8001"
echo "  - Redis: localhost:6379"
echo ""
echo "Next steps:"
echo "1. Initialize database schemas: source venv/bin/activate && python scripts/init_databases.py"
echo "2. Load Seattle data: python scripts/load_data.py"
echo ""
