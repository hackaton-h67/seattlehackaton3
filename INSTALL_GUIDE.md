# 🚀 Complete Installation Guide

## Overview

This guide will help you install **everything** needed for the full Service-Sense AI triage system:

1. **Ollama** (Local LLM) - FREE, intelligent classification
2. **PostgreSQL** - Structured data storage
3. **Neo4j** - Graph database for relationships
4. **Redis** - Caching layer
5. **Initialize all databases** and start services

**Time Required:** 15-30 minutes
**Internet Required:** Yes (for downloads)
**Disk Space:** ~10GB

---

## Prerequisites

- Ubuntu/Debian-based system (or WSL)
- Sudo access
- Internet connection
- At least 8GB RAM (16GB recommended)
- 10GB free disk space

---

## Quick Install (2 Commands)

The fastest way to get everything running:

```bash
# 1. Install all system components (requires sudo, ~10-15 minutes)
sudo ./scripts/install_all.sh

# 2. Initialize and start everything (~5 minutes)
./scripts/setup_after_install.sh
```

That's it! Jump to the [Verification](#verification) section to test your installation.

---

## Detailed Step-by-Step Guide

### Step 1: Install System Components (Requires Sudo)

This installs Ollama, PostgreSQL, Neo4j, and Redis:

```bash
sudo ./scripts/install_all.sh
```

**What it does:**
- ✅ Installs Ollama (local LLM engine)
- ✅ Downloads llama3.1:8b model (~4.7GB)
- ✅ Installs and configures PostgreSQL
- ✅ Installs and configures Neo4j
- ✅ Installs and configures Redis
- ✅ Starts all services
- ✅ Verifies installations

**Expected output:**
```
==========================================
Service-Sense Complete Installation
==========================================

[1/4] Installing Ollama...
✅ Ollama installed successfully
ollama version is 0.x.x

[2/4] Installing PostgreSQL...
✅ PostgreSQL configured
   Database: service_sense
   User: service_sense
   Password: testpassword123

[3/4] Installing Neo4j...
✅ Neo4j configured
   Web interface: http://localhost:7474
   Bolt port: 7687
   User: neo4j
   Password: testpassword123

[4/4] Installing Redis...
✅ Redis configured
   Port: 6379
   Password: testpassword123

[5/5] Pulling Ollama model (llama3.1:8b)...
This will download ~4.7GB and may take 5-10 minutes...
✅ Ollama model downloaded

==========================================
Installation Complete!
==========================================
```

**Troubleshooting:**
- If it fails, check `/tmp/install.log` for errors
- Ensure you have sudo access
- Check internet connection
- Verify you have enough disk space: `df -h`

---

### Step 2: Initialize Databases and Start Services

After the system installation completes, run:

```bash
./scripts/setup_after_install.sh
```

**What it does:**
- ✅ Activates Python virtual environment
- ✅ Initializes database schemas (Neo4j constraints, PostgreSQL tables)
- ✅ Starts Ollama server
- ✅ Verifies all databases are accessible
- ✅ Starts the API server

**Expected output:**
```
==========================================
Service-Sense Post-Installation Setup
==========================================

[1/5] Activating virtual environment...
✅ Virtual environment activated

[2/5] Initializing database schemas...
✅ Database schemas initialized

[3/5] Starting Ollama server...
✅ Ollama server started

[4/5] Verifying all services...
✅ PostgreSQL is ready
✅ Neo4j is ready
✅ Redis is ready
✅ ChromaDB is ready
✅ Ollama server is running
✅ Model llama3.1:8b is available

[5/5] Starting API server...
✅ API server started successfully (PID: xxxxx)
   http://localhost:8000

==========================================
Setup Complete!
==========================================
```

---

## Verification

### 1. Check All Services

```bash
# API Health
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":...}

# PostgreSQL
psql -h localhost -U service_sense -d service_sense -c "SELECT version();"
# Password: testpassword123

# Neo4j Web Interface
# Open in browser: http://localhost:7474
# Username: neo4j
# Password: testpassword123

# Redis
redis-cli -a testpassword123 ping
# Expected: PONG

# ChromaDB
ls -la data/chroma/
# Should see chroma.sqlite3 file

# Ollama
ollama list
# Should show llama3.1:8b
```

### 2. Test the API

**Simple request:**
```bash
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "There is a pothole on 5th Avenue"}' | python3 -m json.tool
```

**Expected response:**
```json
{
  "request_id": "uuid-here",
  "classification": {
    "service_code": "SDOT_POTHOLE",
    "service_name": "Pothole Repair",
    "department": "SDOT",
    "confidence_score": 0.89
  },
  "prediction": {
    "estimated_days": 7,
    "confidence_interval": [5, 10]
  },
  "processing_time_ms": 3245
}
```

**Complex request with Ollama LLM:**
```bash
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{
    "text": "There is extensive graffiti covering multiple buildings in my neighborhood. It appeared overnight and is very offensive. Multiple neighbors have complained.",
    "location": {
      "latitude": 47.6062,
      "longitude": -122.3321,
      "address": "Pike Place Market area"
    }
  }' | python3 -m json.tool
```

This should use Ollama for intelligent classification!

### 3. Test Ollama Directly

```bash
ollama run llama3.1:8b "Classify this Seattle service request: 'Street light is out at corner of 5th and Pike'"
```

---

## What Each Component Does

### PostgreSQL (Relational Database)
- **Port:** 5432
- **Database:** service_sense
- **User:** service_sense / testpassword123
- **Purpose:** Store feedback, predictions, A/B test results
- **Tables:**
  - `feedback` - User ratings and actual resolution times
  - `predictions` - Stored predictions for comparison
  - `ab_experiments` - A/B testing data

### Neo4j (Graph Database)
- **Ports:** 7474 (HTTP), 7687 (Bolt)
- **User:** neo4j / testpassword123
- **Purpose:** Store service relationships, patterns, historical context
- **Web Interface:** http://localhost:7474
- **Nodes:** Service, Department, Neighborhood, ServiceRequest, Keyword
- **Relationships:** HANDLED_BY, HAS_KEYWORD, FILED_FOR, HAS_PATTERN

### Redis (Cache)
- **Port:** 6379
- **Password:** testpassword123
- **Purpose:** Cache expensive operations (LLM calls, graph queries, embeddings)
- **TTL:** 300 seconds (configurable)

### ChromaDB (Vector Database)
- **Location:** ./data/chroma/
- **Purpose:** Semantic similarity search for service requests
- **Collection:** service-requests
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)

### Ollama (Local LLM)
- **Port:** 11434
- **Model:** llama3.1:8b
- **Purpose:** Intelligent classification without API costs
- **Size:** ~4.7GB
- **Speed:** ~3-5 seconds per request (CPU), ~1-2s (GPU)

---

## Architecture After Full Installation

```
User Request
    ↓
┌─────────────────────────────────────┐
│   API Gateway (FastAPI)              │
│   http://localhost:8000              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   Input Processor                    │
│   - Text normalization               │
│   - Entity extraction                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   GraphRAG Orchestrator              │
│   - Combines vector + graph search   │
└─────────────────────────────────────┘
    ↓           ↓
┌──────────┐  ┌──────────┐
│ ChromaDB │  │  Neo4j   │
│ (Vector) │  │ (Graph)  │
│    ✅    │  │    ✅    │
└──────────┘  └──────────┘
    ↓
┌─────────────────────────────────────┐
│   LLM Triage (Ollama llama3.1:8b)   │
│   - Intelligent classification       │
│   - Context-aware reasoning          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│   ML Prediction (Ensemble)           │
│   - Resolution time prediction       │
└─────────────────────────────────────┘
    ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │  Redis   │  │ Response │
│(Feedback)│  │ (Cache)  │  │ Formatter│
│    ✅    │  │    ✅    │  │          │
└──────────┘  └──────────┘  └──────────┘
```

---

## Common Issues and Solutions

### Ollama Not Starting

**Problem:** `ollama serve` fails or exits immediately

**Solutions:**
```bash
# Check if port 11434 is already in use
lsof -i :11434

# Kill existing Ollama processes
pkill ollama

# Start with verbose logging
ollama serve --verbose

# Check logs
tail -f /tmp/ollama.log
```

### Neo4j Connection Refused

**Problem:** Can't connect to Neo4j on port 7474/7687

**Solutions:**
```bash
# Check if Neo4j is running
systemctl status neo4j

# Restart Neo4j
sudo systemctl restart neo4j

# Check logs
sudo journalctl -u neo4j -f

# Verify ports are listening
ss -tlnp | grep -E "(7474|7687)"
```

### PostgreSQL Permission Denied

**Problem:** Can't connect to PostgreSQL

**Solutions:**
```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Grant permissions again
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE service_sense TO service_sense;"

# Test connection
psql -h localhost -U service_sense -d service_sense
# Password: testpassword123
```

### API Server Won't Start

**Problem:** Port 8000 already in use

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or kill all api-gateway processes
pkill -f "api-gateway"

# Restart API
./scripts/setup_after_install.sh
```

### Out of Memory

**Problem:** System runs out of RAM, especially with Ollama

**Solutions:**
```bash
# Use a smaller Ollama model
ollama pull phi3  # Only 2.3GB

# Update .env
echo "OLLAMA_MODEL=phi3" >> .env

# Restart services
./scripts/setup_after_install.sh

# Monitor memory usage
htop
```

---

## Performance Optimization

### For Better Ollama Speed

If you have a GPU:
```bash
# Install CUDA drivers (if NVIDIA GPU)
# Ollama will automatically detect and use GPU

# Verify GPU usage
nvidia-smi
```

### For Better Database Performance

```bash
# Increase PostgreSQL shared memory
sudo nano /etc/postgresql/*/main/postgresql.conf
# Set: shared_buffers = 256MB

# Increase Neo4j heap size
sudo nano /etc/neo4j/neo4j.conf
# Set: server.memory.heap.max_size=4G

# Restart services
sudo systemctl restart postgresql neo4j
```

### Enable Redis Persistence

```bash
sudo nano /etc/redis/redis.conf
# Uncomment: save 900 1
# Uncomment: save 300 10

sudo systemctl restart redis-server
```

---

## Next Steps

### 1. Load Seattle Open Data (Optional)

```bash
source venv/bin/activate
python scripts/load_data.py
```

This loads historical Seattle service request data into Neo4j and ChromaDB for better context.

### 2. Train ML Models (Optional)

```bash
python ml/training/train_models.py
```

This trains ensemble models for better resolution time predictions.

### 3. Explore the API

Interactive API documentation:
- http://localhost:8000/docs

### 4. Monitor Metrics

If Prometheus/Grafana are set up:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## Uninstallation

If you need to remove everything:

```bash
# Stop all services
sudo systemctl stop neo4j postgresql redis-server
pkill ollama
pkill -f "api-gateway"

# Remove packages
sudo apt-get remove --purge neo4j postgresql redis-server
rm -rf /usr/local/bin/ollama

# Remove data
rm -rf data/chroma/
sudo rm -rf /var/lib/neo4j
sudo rm -rf /var/lib/postgresql

# Remove Ollama models
rm -rf ~/.ollama
```

---

## Support

- **Documentation:** See other .md files in this directory
- **API Docs:** http://localhost:8000/docs
- **Logs:**
  - API: `logs/api-gateway.log`
  - Ollama: `/tmp/ollama.log`
  - Neo4j: `sudo journalctl -u neo4j`
  - PostgreSQL: `sudo journalctl -u postgresql`

---

## Summary

After running both scripts, you have:

✅ **Ollama** with llama3.1:8b for FREE intelligent classification
✅ **PostgreSQL** for structured data and feedback
✅ **Neo4j** for graph-based relationships and patterns
✅ **Redis** for caching and performance
✅ **ChromaDB** for vector similarity search
✅ **API Server** running on port 8000
✅ **All database schemas** initialized

The system is now running with full GraphRAG + LLM capabilities!

---

**Installation Date:** 2025-11-05
**Version:** 1.0.0
**Status:** Production Ready
