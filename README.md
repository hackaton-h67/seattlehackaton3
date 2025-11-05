# Service-Sense: Intelligent Triage & Predictive Resolution System

An AI-powered system that transforms Seattle's customer service request system into a transparent, predictive, data-driven experience using a hybrid GraphRAG + ML architecture.

## Overview

Service-Sense provides:
- **Intelligent Triage**: Automatic categorization to the correct department
- **Predictive Resolution Times**: ML-powered predictions with confidence intervals
- **Transparent Reasoning**: Clear justifications based on historical data
- **Multimodal Input**: Text and voice input support (English only)

## Target Metrics
- **Triage Accuracy**: >95% correct department routing
- **Prediction Accuracy**: ±3 days MAE for resolution times
- **Response Time**: <500ms API response
- **User Satisfaction**: >85% accuracy rating

## Architecture

This system uses a microservices architecture:

```
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
    ┌────┴────────────────────────────┐
    ▼                                 ▼
┌──────────────────┐        ┌──────────────────┐
│ Input Processor  │        │ Entity Extractor │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         └──────────┬────────────────┘
                    ▼
         ┌──────────────────────┐
         │ GraphRAG Orchestrator│
         └──────────┬───────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌─────────┐         ┌──────────┐
    │ChromaDB │         │  Neo4j   │
    └─────────┘         └──────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌─────────────────┐
         │   LLM Triage    │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │ ML Prediction   │
         └────────┬────────┘
                  ▼
         ┌─────────────────┐
         │Response Formatter│
         └─────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- 16GB RAM minimum
- GPU (optional, for WhisperX)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd seattlehackaton3
```

2. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start all services:
```bash
docker-compose up -d
```

4. Initialize the databases:
```bash
python scripts/init_databases.py
```

5. Load Seattle Open Data:
```bash
python scripts/load_data.py
```

6. Train initial ML models:
```bash
python ml/training/train_models.py
```

### Development Setup

For local development:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run services individually
cd services/api-gateway
uvicorn main:app --reload --port 8000
```

## Project Structure

```
.
├── services/              # Microservices
│   ├── api-gateway/      # Main API entry point
│   ├── input-processor/  # Text/audio processing
│   ├── entity-extraction/# Entity extraction
│   ├── graphrag-orchestrator/  # Hybrid retrieval
│   ├── vector-search/    # ChromaDB service
│   ├── graph-query/      # Neo4j service
│   ├── llm-triage/       # LLM classification
│   ├── ml-prediction/    # ML prediction models
│   └── response-formatter/  # Response generation
├── shared/               # Shared libraries
│   ├── models/          # Data models
│   ├── utils/           # Utility functions
│   └── config/          # Configuration
├── ml/                  # Machine learning
│   ├── models/          # Trained models
│   ├── training/        # Training scripts
│   └── evaluation/      # Evaluation scripts
├── data/                # Data storage
│   ├── raw/            # Raw datasets
│   └── processed/      # Processed data
├── infra/              # Infrastructure
│   ├── neo4j/         # Neo4j setup
│   ├── chromadb/      # ChromaDB setup
│   └── monitoring/    # Monitoring stack
├── tests/              # Tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/            # Utility scripts
└── docs/              # Documentation
```

## API Usage

### Triage a Service Request

```bash
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{
    "text": "There is a huge pothole on 5th and Pine that damaged my car",
    "location": {
      "latitude": 47.6115,
      "longitude": -122.3344
    }
  }'
```

### Response Format

```json
{
  "request_id": "uuid",
  "classification": {
    "service_code": "SDOT_POTHOLE",
    "service_name": "Pothole Repair",
    "department": "SDOT",
    "confidence_score": 0.96
  },
  "prediction": {
    "expected_resolution_days": 7.5,
    "confidence_interval_90": {
      "lower_bound": 4.2,
      "upper_bound": 10.8
    }
  },
  "reasoning": {
    "classification_reasoning": "Request mentions vehicle damage at specific intersection, matches historical pothole reports in downtown area.",
    "similar_requests": [...]
  }
}
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# All tests with coverage
pytest --cov=services --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy services/
```

## Deployment

See [docs/deployment.md](docs/deployment.md) for production deployment instructions.

## Monitoring

Access monitoring dashboards:
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- API Docs: http://localhost:8000/docs

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

For issues and questions, please open a GitHub issue.
