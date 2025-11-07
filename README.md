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
- Python 3.11+
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

### Installation (2 minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd seattlehackaton3

# 2. Run automated installer
chmod +x install.sh
./install.sh

# 3. Start API server
./start_api.sh
```

The system is now running at http://localhost:8000

**For detailed installation options**, see [INSTALLATION.md](INSTALLATION.md)

### Optional Enhancements

**Add Ollama (Free Local LLM):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
ollama serve
```

**Add Full Database Support:**
```bash
# Start databases
docker-compose up -d postgres neo4j chromadb redis

# Initialize schemas
python scripts/init_databases.py

# Load Seattle service request data (3,811 records)
python scripts/load_data.py

# Verify data loaded successfully
python scripts/verify_data.py
```

See [INSTALLATION.md](INSTALLATION.md) for complete instructions and [DATA_LOADING_GUIDE.md](DATA_LOADING_GUIDE.md) for data loading details.

### Frontend Setup

The frontend provides Citizen Portal, Admin Dashboard, and Demo interfaces.

```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:3001
```

See [frontend/README.md](frontend/README.md) for detailed documentation.

## Project Structure

```
.
├── frontend/            # React frontend (NEW!)
│   ├── src/
│   │   ├── pages/      # Citizen Portal, Admin, Demo
│   │   ├── components/ # Reusable UI components
│   │   ├── services/   # API integration
│   │   └── types/      # TypeScript types
│   ├── Dockerfile      # Production build
│   └── README.md       # Frontend docs
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
│   ├── init_databases.py      # Initialize database schemas
│   ├── load_data.py           # Load Seattle Open Data
│   ├── verify_data.py         # Verify data loaded successfully
│   ├── test_load_small.py     # Test with small data sample
│   └── run_full_load.sh       # Interactive data loading script
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
pytest tests/ -v                    # All tests
pytest --cov=services --cov=shared  # With coverage
```

### Code Quality

```bash
make format    # Format code
make lint      # Lint and type check
```

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## Monitoring

- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Neo4j Browser: http://localhost:7474

## Documentation

- [INSTALLATION.md](INSTALLATION.md) - Complete installation guide
- [DATA_LOADING_GUIDE.md](DATA_LOADING_GUIDE.md) - Guide for loading Seattle Open Data
- [CLAUDE.md](CLAUDE.md) - Development guide for Claude Code
- [PRD.md](PRD.md) - Product requirements document
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Executive project summary
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Implementation details
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security considerations
- [TEST_REPORT.md](TEST_REPORT.md) - Test results and coverage

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Support

For issues and questions, please open a GitHub issue.
