# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Service-Sense is an AI-powered triage system for Seattle's customer service requests. It uses a **hybrid GraphRAG + ML architecture** to:
1. Classify citizen requests to the correct department (>95% accuracy target)
2. Predict resolution times with confidence intervals (±3 days MAE target)
3. Provide transparent reasoning based on historical data

**Key constraint**: English-only support in this version.

## Build and Development Commands

```bash
# Setup
pip install -e .                    # Install production dependencies
pip install -e ".[dev]"             # Install dev dependencies
make dev-install                    # Install dev deps + pre-commit hooks

# Docker infrastructure
docker-compose up -d                # Start all services
docker-compose up -d postgres neo4j chromadb redis  # Start only databases
docker-compose logs -f <service>    # View logs for specific service
docker-compose down -v              # Stop and remove volumes

# Database initialization
python scripts/init_databases.py    # Create schemas in Neo4j, ChromaDB, PostgreSQL
python scripts/load_data.py         # Load Seattle Open Data (dataset: 5ngg-rpne)

# ML training
python ml/training/train_models.py  # Train ensemble prediction models

# Running services
make run-api                        # Run API gateway locally
cd services/<service> && python main.py  # Run individual service

# Testing
pytest tests/ -v                    # All tests
pytest tests/unit/ -v               # Unit tests only
pytest tests/integration/ -v        # Integration tests
pytest tests/e2e/ -v                # End-to-end tests
pytest -k test_name                 # Run specific test
pytest --cov=services --cov=shared  # With coverage

# Code quality
make format                         # Black + Ruff auto-fix
make lint                           # Ruff + MyPy checks
black .                            # Format code (line length: 100)
ruff check .                       # Lint
mypy services/ shared/             # Type check
```

## Architecture: Microservices + GraphRAG + ML

### Request Flow
```
User Request → API Gateway → Input Processor (text/audio) → Entity Extraction
                                                            ↓
                                          GraphRAG Orchestrator
                                         /                    \
                               Vector Search            Graph Query
                              (ChromaDB)                (Neo4j)
                                         \                    /
                                          LLM Triage (Claude/GPT-4)
                                                    ↓
                                          ML Prediction (Ensemble)
                                                    ↓
                                          Response Formatter
```

### Critical Services

**API Gateway** (`services/api-gateway/main.py`): FastAPI entry point. Main endpoint: `POST /api/v2/triage`. Uses middleware for metrics tracking and CORS.

**GraphRAG Orchestrator**: Combines vector search (semantic similarity) and graph search (relationships) to provide context to LLM. This is the key differentiator from simple RAG.

**LLM Triage**: Uses Claude Sonnet 4.5 or GPT-4 with structured prompts. Returns JSON with service_code, classification reasoning, and alternatives.

**ML Prediction**: Ensemble of 4 models (Linear, RandomForest, GradientBoosting, MLP) for resolution time prediction with 90% confidence intervals.

### Data Models

All Pydantic models are in `shared/models/`:
- `TriageRequest`: Input (text/audio, location, user_context)
- `TriageResponse`: Output with Classification, Prediction, Reasoning
- `ExtractedEntities`: Structured data from NLP (location_type, service_keywords, urgency_indicators, damage_severity)
- `ProcessedInput`: Normalized text with confidence score

### Configuration

**Settings singleton**: `shared/config/settings.py` loads from `.env` via Pydantic. Access via `from shared.config.settings import settings`.

**Feature flags**: Control which components are enabled (e.g., `enable_audio_input`, `enable_graph_search`, `mock_llm`).

**Database connection strings**: Constructed via properties (`settings.postgres_url`, `settings.redis_url`, `settings.chroma_url`).

## Database Architecture

### Neo4j Graph Schema
- **Nodes**: Service, Department, Neighborhood, ServiceRequest, Keyword, Season, ResolutionPattern
- **Key relationships**:
  - `(Service)-[:HANDLED_BY]->(Department)`
  - `(Service)-[:HAS_KEYWORD]->(Keyword)`
  - `(ServiceRequest)-[:FILED_FOR]->(Service)`
  - `(Service)-[:HAS_PATTERN]->(ResolutionPattern)`
- **Indexes**: Constraints on unique IDs, indexes on names and dates
- **Purpose**: Encode domain knowledge and relationships for graph queries

### ChromaDB Collections
- **Collection name**: `service-requests` (configurable via `settings.chroma_collection`)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Purpose**: Semantic similarity search for historical requests

### PostgreSQL Tables
- `feedback`: User ratings and actual resolution times (for model retraining)
- `predictions`: Stored predictions for comparison
- `ab_experiments`: A/B testing data

### Redis
- **Purpose**: Caching layer for expensive operations (graph queries, embeddings, LLM responses)
- **TTL**: 300 seconds default (`settings.cache_ttl_seconds`)

## Implementation Priorities

### Phase 1: MVP (Core Pipeline)
1. Complete `services/input-processor/main.py`: Text normalization (audio can be mocked)
2. Implement `services/entity-extraction/`: Extract entities using LLM or NLP library
3. Implement `services/llm-triage/`: Classification with prompt from PRD section 7.1
4. Implement `services/response-formatter/`: Format TriageResponse

### Phase 2: GraphRAG
5. `services/vector-search/`: ChromaDB similarity search
6. `services/graph-query/`: Cypher queries for Neo4j patterns
7. `services/graphrag-orchestrator/`: Merge vector + graph context, pass to LLM

### Phase 3: ML Prediction
8. Feature engineering in `ml/training/`: Temporal, location, historical features
9. Train ensemble models with proper validation
10. Deploy models to `services/ml-prediction/`

## Key Technical Decisions

### Why GraphRAG over RAG?
Graph database captures **structural relationships** (which department handles which service, which services are common in which neighborhoods) that pure vector search misses. Hybrid retrieval improves classification accuracy.

### Why Ensemble ML?
Single models overfit or have high variance. Ensemble (4 models with learned weights) provides better predictions and enables confidence intervals via prediction variance.

### Async/Await Pattern
All I/O operations (DB queries, LLM calls, HTTP requests) use `async`/`await`. Services communicate via async HTTP or direct async function calls.

### Structured Logging
Uses `structlog` for JSON logging with context. Log format: `logger.info("event_name", key=value)`. Never use print() in services.

### Metrics
Prometheus metrics via `shared/utils/metrics.py`. Track: triage_accuracy, prediction_mae, api_response_time, error_rate. Access via Grafana on port 3000.

## Seattle Open Data Integration

**Dataset**: Customer Service Requests (5ngg-rpne)
**Fields**: 16 fields including servicerequestnumber, webintakeservicerequests, departmentname, createddate, location, latitude/longitude, councildistrict, neighborhood
**API**: `https://data.seattle.gov/resource/5ngg-rpne.json`
**Loading**: `scripts/load_data.py` fetches in batches (1000 records), transforms, loads to Neo4j + ChromaDB

## Testing Patterns

### Unit Tests
Mock external dependencies (databases, LLM APIs). Test individual functions/classes in isolation.

### Integration Tests
Spin up test databases (use Docker test containers). Test service-to-service communication.

### E2E Tests
Full pipeline test: Send TriageRequest → verify TriageResponse structure and data quality.

### Fixtures
Use pytest fixtures for common test data (sample TriageRequest, mock settings, test database connections).

## Common Patterns

### Adding a New Service
1. Create `services/<service-name>/main.py` with main logic
2. Add `services/<service-name>/Dockerfile` (copy from existing service)
3. Add service to `docker-compose.yml` with dependencies
4. Import shared models: `from shared.models.request import ...`
5. Use settings: `from shared.config.settings import settings`
6. Add logging: `from shared.utils.logging import get_logger; logger = get_logger(__name__)`

### Adding a New Endpoint
1. Add route to `services/api-gateway/main.py`
2. Define request/response models in `shared/models/`
3. Implement business logic (call other services)
4. Add integration test in `tests/integration/`
5. Update OpenAPI docs (FastAPI generates automatically)

### LLM Prompt Engineering
Prompts are in PRD (`service-sense-enhanced-prd-english-only(1).md`):
- **TRIAGE_PROMPT**: Section 7.1 - Classification with JSON output
- **EXTRACTION_PROMPT**: Section 3.2 - Entity extraction
- **CONTEXT_ENHANCEMENT_PROMPT**: Section 7.2 - Implicit context

Format: Pass retrieved context + user input → LLM → Parse JSON response

### Feature Engineering for ML
Features from PRD section 5.1:
- **Categorical**: service_code, department, method_received (encode via label encoding)
- **Temporal**: month, day_of_week, quarter, is_weekend
- **Location**: council_district, zipcode_income_level, neighborhood_density
- **Historical**: dept_avg_resolution, neighborhood_avg_resolution, service_complexity
- **Interaction**: dept_neighborhood_interaction

Store in `ml/training/feature_engineering.py`.

## Monitoring and Debugging

### Access Points
- API docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/password from .env)
- Prometheus: http://localhost:9090
- Neo4j Browser: http://localhost:7474 (neo4j/password from .env)

### Debugging Services
```bash
docker-compose logs -f <service-name>  # View logs
docker exec -it service-sense-postgres psql -U service_sense  # PostgreSQL
docker exec -it service-sense-redis redis-cli  # Redis
```

### Health Checks
All services have health check endpoints. Check `docker-compose ps` to verify all services are "healthy" before debugging application logic.

## Production Considerations

- Change all default passwords in `.env` (NEO4J_PASSWORD, POSTGRES_PASSWORD, REDIS_PASSWORD, GRAFANA_ADMIN_PASSWORD)
- Set `SECRET_KEY` to a secure random value
- Configure CORS origins properly (`cors_origins` in settings)
- Enable `enable_api_key_auth` and set `API_KEY` for authentication
- Use production WSGI server (already using uvicorn with workers)
- Set up proper backup strategies for databases
- Configure monitoring alerts in Grafana
- Use managed database services (RDS, Aiven) instead of Docker containers
