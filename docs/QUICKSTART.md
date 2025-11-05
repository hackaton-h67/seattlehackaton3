# Quick Start Guide

This guide will help you get Service-Sense up and running quickly.

## Prerequisites

- Docker Desktop or Docker + Docker Compose
- Python 3.11 or higher
- 16GB RAM (minimum)
- API keys (optional for initial testing):
  - Anthropic API key (for Claude)
  - OpenAI API key (for GPT-4)
  - Seattle Open Data App Token (optional, but recommended)

## Step-by-Step Setup

### 1. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum required settings:**
```env
# At least one LLM provider
ANTHROPIC_API_KEY=your_key_here

# Database passwords (change these!)
NEO4J_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_secure_password
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### 2. Start Infrastructure

```bash
# Start all databases and infrastructure
docker-compose up -d postgres neo4j chromadb redis

# Check that all services are healthy
docker-compose ps

# You should see all services as "healthy"
```

### 3. Initialize Databases

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Initialize database schemas
python scripts/init_databases.py
```

Expected output:
```
INFO: initializing_neo4j
INFO: created_constraint ...
INFO: neo4j_initialized
INFO: chromadb_initialized
INFO: postgres_initialized
```

### 4. Load Sample Data (Optional)

```bash
# Load Seattle Open Data
python scripts/load_data.py

# This will fetch and load service request data
# Initial load may take 10-15 minutes
```

### 5. Start the API

Option A: Using Docker Compose (recommended)
```bash
docker-compose up api-gateway
```

Option B: Running locally for development
```bash
cd services/api-gateway
uvicorn main:app --reload --port 8000
```

### 6. Test the API

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Or use curl:
```bash
# Health check
curl http://localhost:8000/health

# Test triage endpoint
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{
    "text": "There is a pothole on 5th Avenue",
    "location": {
      "latitude": 47.6062,
      "longitude": -122.3321
    }
  }'
```

## Next Steps

### Development Mode

Use the `/init` Claude Code command for guided implementation:
```
/init
```

This will help you:
1. Set up your development environment
2. Choose which components to implement first
3. Get step-by-step guidance on implementation

### Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000 (admin/your_password)
- **Prometheus**: http://localhost:9090
- **Neo4j Browser**: http://localhost:7474 (neo4j/your_password)

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov=shared
```

## Common Issues

### Docker containers not starting

```bash
# Check logs
docker-compose logs <service-name>

# Restart a specific service
docker-compose restart <service-name>

# Full cleanup and restart
docker-compose down -v
docker-compose up -d
```

### Database connection errors

1. Ensure containers are healthy: `docker-compose ps`
2. Check passwords in `.env` match docker-compose.yml
3. Wait 30 seconds after `docker-compose up` for databases to initialize

### Import errors when running Python

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

### Port conflicts

If ports 5432, 6379, 7474, 7687, 8000, 8001, or 9090 are in use:
1. Stop conflicting services
2. Or modify port mappings in `docker-compose.yml`

## Development Workflow

1. **Start databases**: `docker-compose up -d postgres neo4j chromadb redis`
2. **Run a service locally**: `cd services/<service-name> && python main.py`
3. **Make changes** and test
4. **Run tests**: `pytest`
5. **Format code**: `make format`
6. **Commit**: Follow conventional commit format

## Getting Help

- Read the PRD: `service-sense-enhanced-prd-english-only(1).md`
- Check the README: `README.md`
- Use the `/init` command in Claude Code
- Review the architecture in `docker-compose.yml`

## Production Deployment

For production deployment, see `docs/deployment.md` (to be created).

Key considerations:
- Use proper secrets management
- Set up SSL/TLS certificates
- Configure proper backup strategies
- Set up monitoring alerts
- Use production-grade database instances
- Enable rate limiting
- Configure CORS properly
