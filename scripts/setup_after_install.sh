#!/bin/bash
# Post-Installation Setup Script
# Run this AFTER install_all.sh completes
# This script does NOT require sudo

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Service-Sense Post-Installation Setup"
echo "==========================================${NC}"
echo ""

# Get project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Working directory: $PROJECT_DIR"
echo ""

# ============================================
# 1. Activate virtual environment
# ============================================
echo -e "${BLUE}[1/5] Activating virtual environment...${NC}"

if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# ============================================
# 2. Initialize database schemas
# ============================================
echo -e "${BLUE}[2/5] Initializing database schemas...${NC}"
echo "This will create tables, indexes, and constraints..."
echo ""

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

python scripts/init_databases.py

echo -e "${GREEN}✅ Database schemas initialized${NC}"
echo ""

# ============================================
# 3. Start Ollama server
# ============================================
echo -e "${BLUE}[3/5] Starting Ollama server...${NC}"

if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama already running${NC}"
else
    echo "Starting Ollama in background..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3

    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✅ Ollama server started${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama failed to start, check /tmp/ollama.log${NC}"
    fi
fi
echo ""

# ============================================
# 4. Verify all services
# ============================================
echo -e "${BLUE}[4/5] Verifying all services...${NC}"
echo ""

# PostgreSQL
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
    psql -h localhost -U service_sense -d service_sense -c "SELECT COUNT(*) FROM feedback;" 2>/dev/null || echo "   (Tables created, no data yet)"
else
    echo -e "${RED}❌ PostgreSQL is not accessible${NC}"
fi

# Neo4j
if curl -s http://localhost:7474 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Neo4j is ready${NC}"
    echo "   Web interface: http://localhost:7474"
else
    echo -e "${RED}❌ Neo4j is not accessible${NC}"
fi

# Redis
if redis-cli -a testpassword123 ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not accessible${NC}"
fi

# ChromaDB
if [ -f "data/chroma/chroma.sqlite3" ]; then
    echo -e "${GREEN}✅ ChromaDB is ready${NC}"
    echo "   Data directory: data/chroma/"
else
    echo -e "${YELLOW}⚠️  ChromaDB data not found, reinitializing...${NC}"
    python scripts/init_chromadb_embedded.py
fi

# Ollama
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama server is running${NC}"
    if ollama list 2>/dev/null | grep -q "llama3.1:8b"; then
        echo -e "${GREEN}✅ Model llama3.1:8b is available${NC}"
    else
        echo -e "${YELLOW}⚠️  Model llama3.1:8b not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama server not running${NC}"
fi

echo ""

# ============================================
# 5. Kill old API servers and start new one
# ============================================
echo -e "${BLUE}[5/5] Starting API server...${NC}"

# Kill any running API servers
echo "Stopping old API servers..."
pkill -f "api-gateway" 2>/dev/null || true
sleep 2

# Start new API server
echo "Starting new API server..."
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
nohup venv/bin/python services/api-gateway/main.py > logs/api-gateway.log 2>&1 &
API_PID=$!

sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server started successfully (PID: $API_PID)${NC}"
    echo "   http://localhost:8000"
else
    echo -e "${RED}❌ API server failed to start${NC}"
    echo "   Check logs/api-gateway.log for errors"
fi

echo ""

# ============================================
# Summary
# ============================================
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Service Status:"
echo "  📊 PostgreSQL: http://localhost:5432"
echo "  🔗 Neo4j: http://localhost:7474"
echo "  ⚡ Redis: localhost:6379"
echo "  🗄️  ChromaDB: data/chroma/"
echo "  🦙 Ollama: http://localhost:11434"
echo "  🚀 API Gateway: http://localhost:8000"
echo ""
echo "Quick Tests:"
echo ""
echo "1. API Health:"
echo "   curl http://localhost:8000/health"
echo ""
echo "2. Simple Triage Request:"
echo '   curl -X POST http://localhost:8000/api/v2/triage \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"text": "Pothole on 5th Avenue"}'"'"' | python3 -m json.tool'
echo ""
echo "3. Complex Request with Location:"
echo '   curl -X POST http://localhost:8000/api/v2/triage \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{
    "text": "There is extensive graffiti on multiple buildings near Pike Place Market",
    "location": {"latitude": 47.6062, "longitude": -122.3321}
  }'"'"' | python3 -m json.tool'
echo ""
echo "4. Test Ollama directly:"
echo '   ollama run llama3.1:8b "Classify this: pothole on street"'
echo ""
echo "Documentation:"
echo "  📖 SETUP_COMPLETE.md - Overview and status"
echo "  📖 DATABASE_STATUS.md - Database details"
echo "  📖 OLLAMA_INTEGRATION.md - LLM provider guide"
echo ""
echo -e "${BLUE}System is ready for use!${NC}"
echo ""
