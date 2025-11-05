# Setup Guide: Ollama & Databases

## 🦙 Ollama Setup (Local LLM - Free!)

Ollama lets you run powerful LLMs locally without API costs.

### Install Ollama

```bash
# Linux/WSL
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com/download
```

### Start Ollama Service

```bash
ollama serve
```

### Pull a Model

```bash
# Recommended models:
ollama pull llama3.1:8b      # Fast, good quality (4.7GB)
ollama pull mistral          # Alternative (4.1GB)
ollama pull phi3            # Smaller, faster (2.3GB)

# For better quality (needs more RAM):
ollama pull llama3.1:70b    # Best quality (40GB)
```

### Configure Service-Sense to Use Ollama

The `.env` file is already configured! Just ensure Ollama is running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test the API
curl http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "There is a pothole on 5th Avenue"}'
```

### Ollama Commands

```bash
# List installed models
ollama list

# Run interactive chat (for testing)
ollama run llama3.1:8b

# Remove a model
ollama rm modelname

# Check logs
journalctl -u ollama -f
```

---

## 🗄️ Database Setup

Service-Sense uses 4 databases for full functionality:

### Option 1: Docker (Recommended)

#### Install Docker

```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

#### Start All Databases

```bash
cd /home/hiiamhuywsl/seattlehackaton3

# Start all services
docker-compose up -d postgres neo4j chromadb redis

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Initialize Databases

```bash
# Activate virtual environment
source venv/bin/activate

# Create schemas
python scripts/init_databases.py

# Load Seattle Open Data
python scripts/load_data.py
```

### Option 2: Native Installation (Without Docker)

#### PostgreSQL

```bash
# Install
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE service_sense;
CREATE USER service_sense WITH PASSWORD 'testpassword123';
GRANT ALL PRIVILEGES ON DATABASE service_sense TO service_sense;
EOF
```

#### Neo4j

```bash
# Add repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Install
sudo apt-get update
sudo apt-get install neo4j

# Configure password
sudo neo4j-admin set-initial-password testpassword123

# Start
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Verify
curl http://localhost:7474
```

#### Redis

```bash
# Install
sudo apt-get install redis-server

# Configure password
echo "requirepass testpassword123" | sudo tee -a /etc/redis/redis.conf

# Start
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping
```

#### ChromaDB

ChromaDB runs as a Python service:

```bash
source venv/bin/activate
pip install chromadb

# Start ChromaDB server
chroma run --host localhost --port 8001 &
```

---

## 🔧 Configuration

Update `.env` if using different passwords or hosts:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=testpassword123

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=testpassword123

# Redis
REDIS_PASSWORD=testpassword123

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

---

## ✅ Verification

### Check All Services

```bash
# PostgreSQL
psql -h localhost -U service_sense -d service_sense -c "SELECT version();"

# Neo4j
curl -u neo4j:testpassword123 http://localhost:7474

# Redis
redis-cli -a testpassword123 ping

# ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# Ollama
curl http://localhost:11434/api/tags
```

### Test Service-Sense API

```bash
# Health check
curl http://localhost:8000/health

# Make a triage request with Ollama
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{
    "text": "There is a large pothole on 5th Avenue causing damage to vehicles",
    "location": {"latitude": 47.6062, "longitude": -122.3321}
  }' | python3 -m json.tool
```

---

## 🚀 Quick Start Comparison

### Without Databases (Current)
- ✅ Works immediately
- ⚠️ Fallback classification
- ⚠️ No historical data
- ⚠️ Default predictions (7 days)

### With Ollama Only
- ✅ Free local LLM
- ✅ Intelligent classification
- ⚠️ No historical context
- ⚠️ Default predictions

### With Ollama + Databases (Full Setup)
- ✅ Intelligent classification
- ✅ Historical context (GraphRAG)
- ✅ Similar request matching
- ✅ Accurate predictions from ML
- ✅ Neighborhood patterns
- ✅ Full transparency

---

## 💡 Recommended Setup Order

1. **Start with Ollama** (5 minutes)
   - Free, no registration
   - Much better than fallback

2. **Add Docker + Databases** (30 minutes)
   - Full GraphRAG capabilities
   - Historical data analysis

3. **Train ML Models** (1-2 hours)
   - After loading data
   - Accurate predictions

---

## 🆘 Troubleshooting

### Ollama Not Connecting

```bash
# Check if running
ps aux | grep ollama

# Restart
ollama serve

# Check logs
journalctl -u ollama -f
```

### Database Connection Errors

```bash
# Check Docker containers
docker-compose ps

# Restart specific service
docker-compose restart neo4j

# View logs
docker-compose logs neo4j
```

### Out of Memory with Ollama

```bash
# Use smaller model
ollama pull phi3

# Update .env
OLLAMA_MODEL=phi3
```

### Port Already in Use

```bash
# Find process
sudo lsof -i :8000

# Kill it
kill -9 <PID>
```

---

## 📊 System Requirements

### Minimum (Ollama + Databases)
- RAM: 8GB
- Disk: 20GB free
- CPU: 4 cores

### Recommended
- RAM: 16GB (for llama3.1:8b)
- Disk: 50GB free
- CPU: 8 cores
- GPU: Optional (speeds up Ollama)

### For Large Models (llama3.1:70b)
- RAM: 64GB
- Disk: 100GB free
- CPU: 16+ cores
- GPU: Highly recommended

---

## 🎯 What You Get

| Feature | No Setup | Ollama Only | Full Setup |
|---------|----------|-------------|------------|
| Classification | Keyword | LLM | LLM + Context |
| Historical Data | ❌ | ❌ | ✅ |
| Similar Requests | ❌ | ❌ | ✅ |
| Accurate Predictions | ❌ | ❌ | ✅ |
| Cost | Free | Free | Free |
| Setup Time | 0 min | 5 min | 30 min |

---

**Current Status**: Ollama configured, waiting for installation
**Next Step**: Install Ollama or continue with fallback mode
