# Service-Sense Quick Start Guide

## ✅ Setup Complete!

Your Service-Sense AI triage system is ready to run in development mode.

## What Was Done

1. ✅ Created Python virtual environment
2. ✅ Installed core dependencies (FastAPI, Pydantic, logging, metrics)
3. ✅ Configured environment (.env) with mock mode enabled
4. ✅ Tested all 9 microservices - ALL PASSED
5. ✅ Verified API Gateway structure - READY TO RUN

## Quick Commands

### Start the API Server
```bash
cd /home/hiiamhuywsl/seattlehackaton3
./start_api.sh
```

The server will start on http://localhost:8000

### Test the API
```bash
# Health check
curl http://localhost:8000/health

# Make a triage request
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "There is a pothole on 5th Avenue"}'
```

### View Documentation
Open in browser: http://localhost:8000/docs

## Current Functionality

### ✅ Works Now (No Setup Needed)
- FastAPI server with all endpoints
- Text input processing
- Request validation
- API documentation (Swagger/ReDoc)
- Health monitoring
- Structured logging
- Metrics collection
- Fallback triage (keyword-based)

### ⚠️ Limited (Needs Additional Setup)
- **Entity Extraction**: Rule-based (add API key for LLM)
- **Classification**: Keyword matching (add API key for accurate LLM classification)
- **Predictions**: Default 7 days (needs trained ML models)
- **Historical Data**: None (needs database setup)

## Architecture Status

```
✅ API Gateway          - READY
✅ Input Processor      - FULLY FUNCTIONAL
✅ Entity Extraction    - WORKING (fallback mode)
✅ LLM Triage          - WORKING (fallback mode)
⚠️  GraphRAG            - Needs databases
⚠️  ML Prediction       - Needs trained models
✅ Response Formatter   - READY
```

## Next Steps

### To Get LLM Classification Working
1. Get an Anthropic API key from https://console.anthropic.com
2. Edit `.env` file:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here
   MOCK_LLM=false
   ```
3. Restart the server

### To Add Full Database Support
```bash
# Install Docker (if not available)
# Then:
docker-compose up -d postgres neo4j chromadb redis
python scripts/init_databases.py
python scripts/load_data.py
```

### To Train ML Models
```bash
# After loading data:
python ml/training/train_models.py
```

## Testing

Run the test scripts to verify everything:

```bash
# Basic infrastructure test
python test_basic.py

# Input processor test
python test_input_processor.py

# All services test
python test_all_services.py

# API structure test
python test_api_simple.py
```

## File Structure

```
/home/hiiamhuywsl/seattlehackaton3/
├── .env                      # Configuration (API keys, settings)
├── start_api.sh             # Start script for API
├── venv/                    # Python virtual environment
├── services/                # Microservices
│   ├── api-gateway/         # Main API entry point
│   ├── input-processor/     # Text/audio processing
│   ├── entity-extraction/   # NLP entity extraction
│   ├── llm-triage/         # LLM-based classification
│   └── ...                  # Other services
├── shared/                  # Shared models and utilities
├── scripts/                 # Database init and data loading
└── TEST_RESULTS.md         # Detailed test results
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Module Not Found Errors
```bash
# Activate virtual environment
source venv/bin/activate
# Ensure you're in project root
cd /home/hiiamhuywsl/seattlehackaton3
```

### API Not Responding
```bash
# Check logs
./start_api.sh
# Look for error messages in output
```

## Support

- See `CLAUDE.md` for development guidelines
- See `IMPLEMENTATION_STATUS.md` for feature status
- See `TEST_RESULTS.md` for detailed test results
- See `README.md` for project overview

## Summary

**Status**: ✅ READY FOR DEVELOPMENT

The application is fully functional in mock mode. You can:
1. Start the API server now
2. Make triage requests
3. Get responses with fallback classification
4. Add real API keys and databases later for full functionality

**All core systems are working correctly!**
