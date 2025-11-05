---
description: Initialize the Service-Sense development environment
---

# Service-Sense Initialization

You are helping initialize the Service-Sense development environment. This is an AI-powered triage system for Seattle's customer service requests.

## Current Status

This project is scaffolded but requires implementation of the core components:

### Architecture Overview
- **API Gateway**: FastAPI-based entry point (services/api-gateway/)
- **Input Processor**: Text/audio processing with WhisperX (services/input-processor/)
- **Entity Extraction**: NLP entity extraction (services/entity-extraction/)
- **GraphRAG Orchestrator**: Hybrid vector + graph retrieval (services/graphrag-orchestrator/)
- **Vector Search**: ChromaDB similarity search (services/vector-search/)
- **Graph Query**: Neo4j knowledge graph queries (services/graph-query/)
- **LLM Triage**: Claude/GPT-4 classification (services/llm-triage/)
- **ML Prediction**: Ensemble models for time prediction (services/ml-prediction/)
- **Response Formatter**: Response generation (services/response-formatter/)

### Databases
- **Neo4j**: Graph database for relationships between services, departments, neighborhoods
- **ChromaDB**: Vector database for semantic search of historical requests
- **PostgreSQL**: Application data, feedback, experiments
- **Redis**: Caching layer

## Initialization Tasks

Please complete the following tasks:

### 1. Environment Setup
- Copy `.env.example` to `.env`
- Help the user configure necessary API keys (Anthropic, OpenAI if needed)
- Review and update database credentials

### 2. Database Initialization
- Run `docker-compose up -d postgres neo4j chromadb redis` to start databases
- Wait for health checks to pass
- Run `python scripts/init_databases.py` to create schemas and indexes

### 3. Data Loading
- Review `scripts/load_data.py`
- Help fetch Seattle Open Data (dataset: 5ngg-rpne)
- Load initial dataset into Neo4j and ChromaDB
- Generate embeddings for vector search

### 4. Service Implementation Priority

Focus on implementing services in this order:

#### Phase 1: Basic Pipeline (MVP)
1. **Input Processor**: Complete text normalization (audio can be mocked)
2. **Entity Extraction**: Implement location/keyword extraction
3. **LLM Triage**: Implement classification prompt with Claude
4. **Response Formatter**: Format final responses

#### Phase 2: Enhanced Retrieval
5. **Vector Search**: Implement ChromaDB similarity search
6. **Graph Query**: Implement Neo4j pattern queries
7. **GraphRAG Orchestrator**: Combine vector + graph results

#### Phase 3: ML Prediction
8. **ML Prediction**: Complete ensemble model training
9. **Feature Engineering**: Implement temporal/location features

### 5. Testing
- Run `pytest tests/` to verify basic functionality
- Test the API with sample requests
- Verify database connections

## Key Files to Implement

Based on the PRD (service-sense-enhanced-prd-english-only(1).md), focus on:

1. **Entity Extraction Prompt** (services/entity-extraction/main.py):
   - Extract: location, keywords, urgency, severity
   - Use the EXTRACTION_PROMPT template from PRD section 3.2

2. **LLM Triage Prompt** (services/llm-triage/main.py):
   - Use the TRIAGE_PROMPT from PRD section 7.1
   - Implement JSON output parsing
   - Handle alternative classifications

3. **Neo4j Schema** (infra/neo4j/init/):
   - Implement node types from PRD section 4.1
   - Create relationships from PRD section 4.2

4. **Feature Engineering** (ml/training/feature_engineering.py):
   - Implement features from PRD section 5.1
   - Temporal, location, and historical features

5. **Service Type Mapping** (shared/utils/service_mapping.py):
   - Implement SERVICE_TYPE_MAPPING from PRD section 2.2

## Development Workflow

1. Start with the API Gateway - it's already scaffolded
2. Implement each microservice incrementally
3. Use mock data/responses initially
4. Gradually replace mocks with real implementations
5. Test end-to-end after each service is complete

## Next Steps

Ask the user:
1. What phase they want to start with (MVP, Enhanced, or ML)
2. Which specific service to implement first
3. Whether they have API keys ready
4. If they want to start with mock data or load real Seattle data

Then help them implement that specific component step by step.

## Reference Documents

- PRD: `service-sense-enhanced-prd-english-only(1).md`
- Architecture: See docker-compose.yml for service layout
- Data Schema: PRD section 2.1 (16 fields from Seattle Open Data)
- API Spec: PRD section 6 (OpenAPI 3.0 specification)

Focus on delivering working, tested code for each component before moving to the next.
