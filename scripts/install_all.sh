#!/bin/bash
# Complete Installation Script for Service-Sense
# Installs: Ollama + PostgreSQL + Neo4j + Redis

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Service-Sense Complete Installation"
echo "==========================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run with sudo${NC}"
    echo "Usage: sudo ./scripts/install_all.sh"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo -e "${YELLOW}Installing as user: $ACTUAL_USER${NC}"
echo ""

# ============================================
# 1. Install Ollama
# ============================================
echo -e "${BLUE}[1/4] Installing Ollama...${NC}"

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama already installed${NC}"
    ollama --version
else
    echo "Downloading and installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh

    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✅ Ollama installed successfully${NC}"
        ollama --version
    else
        echo -e "${RED}❌ Ollama installation failed${NC}"
        exit 1
    fi
fi
echo ""

# ============================================
# 2. Install PostgreSQL
# ============================================
echo -e "${BLUE}[2/4] Installing PostgreSQL...${NC}"

if command -v psql &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL already installed${NC}"
    psql --version
else
    apt-get update
    apt-get install -y postgresql postgresql-contrib

    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql

    echo -e "${GREEN}✅ PostgreSQL installed${NC}"
fi

# Create database and user
echo "Setting up database and user..."
sudo -u postgres psql << 'EOF'
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'service_sense') THEN
      CREATE DATABASE service_sense;
   END IF;

   IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'service_sense') THEN
      CREATE USER service_sense WITH PASSWORD 'testpassword123';
   END IF;

   GRANT ALL PRIVILEGES ON DATABASE service_sense TO service_sense;
END
$$;
EOF

echo -e "${GREEN}✅ PostgreSQL configured${NC}"
echo "   Database: service_sense"
echo "   User: service_sense"
echo "   Password: testpassword123"
echo ""

# ============================================
# 3. Install Neo4j
# ============================================
echo -e "${BLUE}[3/4] Installing Neo4j...${NC}"

if command -v neo4j &> /dev/null; then
    echo -e "${GREEN}✅ Neo4j already installed${NC}"
    neo4j version
else
    # Add Neo4j repository
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - 2>/dev/null || true
    echo 'deb https://debian.neo4j.com stable latest' | tee /etc/apt/sources.list.d/neo4j.list

    # Install Neo4j
    apt-get update
    apt-get install -y neo4j

    echo -e "${GREEN}✅ Neo4j installed${NC}"
fi

# Set initial password
echo "Configuring Neo4j password..."
neo4j-admin dbms set-initial-password testpassword123 2>/dev/null || echo "Password already set or neo4j running"

# Start and enable Neo4j
systemctl start neo4j
systemctl enable neo4j

echo -e "${GREEN}✅ Neo4j configured${NC}"
echo "   Web interface: http://localhost:7474"
echo "   Bolt port: 7687"
echo "   User: neo4j"
echo "   Password: testpassword123"
echo ""

# ============================================
# 4. Install Redis
# ============================================
echo -e "${BLUE}[4/4] Installing Redis...${NC}"

if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✅ Redis already installed${NC}"
    redis-cli --version
else
    apt-get update
    apt-get install -y redis-server

    echo -e "${GREEN}✅ Redis installed${NC}"
fi

# Configure password
if ! grep -q "requirepass testpassword123" /etc/redis/redis.conf; then
    echo "requirepass testpassword123" >> /etc/redis/redis.conf
    echo "Configured Redis password"
fi

# Start and enable Redis
systemctl start redis-server
systemctl enable redis-server

echo -e "${GREEN}✅ Redis configured${NC}"
echo "   Port: 6379"
echo "   Password: testpassword123"
echo ""

# ============================================
# 5. Pull Ollama Model
# ============================================
echo -e "${BLUE}[5/5] Pulling Ollama model (llama3.1:8b)...${NC}"
echo "This will download ~4.7GB and may take 5-10 minutes..."
echo ""

# Start Ollama service in background if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server..."
    sudo -u $ACTUAL_USER ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
fi

# Pull model as the actual user
echo "Downloading model..."
sudo -u $ACTUAL_USER ollama pull llama3.1:8b

echo -e "${GREEN}✅ Ollama model downloaded${NC}"
echo ""

# ============================================
# Verification
# ============================================
echo -e "${BLUE}==========================================
Verifying installations...
==========================================${NC}"
echo ""

# PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
fi

# Neo4j
if systemctl is-active --quiet neo4j; then
    echo -e "${GREEN}✅ Neo4j is running${NC}"
else
    echo -e "${RED}❌ Neo4j is not running${NC}"
fi

# Redis
if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running${NC}"
fi

# Ollama
if pgrep -x "ollama" > /dev/null; then
    echo -e "${GREEN}✅ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama not running (will auto-start)${NC}"
fi

# Ollama model
if sudo -u $ACTUAL_USER ollama list | grep -q "llama3.1:8b"; then
    echo -e "${GREEN}✅ Ollama model (llama3.1:8b) is available${NC}"
else
    echo -e "${RED}❌ Ollama model not found${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Installation Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps (run as $ACTUAL_USER):"
echo ""
echo "1. Initialize database schemas:"
echo "   cd $ACTUAL_HOME/seattlehackaton3"
echo "   source venv/bin/activate"
echo "   python scripts/init_databases.py"
echo ""
echo "2. (Optional) Load Seattle Open Data:"
echo "   python scripts/load_data.py"
echo ""
echo "3. Start Ollama server (if not running):"
echo "   ollama serve &"
echo ""
echo "4. Restart the API:"
echo "   ./start_api.sh"
echo ""
echo "5. Test the system:"
echo '   curl -X POST http://localhost:8000/api/v2/triage \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"text": "There is a pothole on 5th Avenue"}'"'"' | python3 -m json.tool'
echo ""
echo -e "${BLUE}All services are ready!${NC}"
echo ""
