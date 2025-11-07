# Data Loading Guide

Complete guide for loading Seattle Open Data into Service-Sense.

## Overview

This guide covers loading Seattle's customer service request data into:
- **Neo4j** - Graph database for relationships
- **ChromaDB** - Vector database for semantic search

## Current Status

**Data Successfully Loaded**: 3,811 Seattle service requests

### What's in the Database

| Database | Content | Count |
|----------|---------|-------|
| Neo4j | Service Requests | 3,811 |
| Neo4j | Services | 5 |
| Neo4j | Departments | 3 |
| ChromaDB | Embedded Documents | 3,811 |

**Service Types**: Abandoned Vehicle, Graffiti Report, Illegal Dumping, Public Place Litter & Recycling, Streetlight Repair

---

## Data Source

**API Endpoint**: `https://data.seattle.gov/resource/43nw-pkdq.json`
- No authentication required
- Public Seattle Customer Service Request data
- Supports batch fetching with `$limit` and `$offset` parameters

### Available Fields

```json
{
  "servicerequestnumber": "21905037",
  "responsibledepartment": "Seattle City Light",
  "servicerequesttype": "Streetlight Repair",
  "reportedlocation": "1806 NE 45TH ST",
  "statuscategory": "In Progress",
  "statusupdate": "Status description...",
  "latitude": "47.6613329573",
  "longitude": "-122.3073645255",
  "updateddate": "2024-12-06T00:00:00.000",
  "statusorder": "3"
}
```

---

## Loading Scripts

### 1. Full Data Load

**Script**: `scripts/load_data.py`

Loads data in batches of 1,000 records (configurable).

```bash
# Interactive script with confirmation
./scripts/run_full_load.sh

# OR direct command
source venv/bin/activate
python scripts/load_data.py
```

**What it does**:
- Fetches data from Seattle Open Data API
- Creates Neo4j nodes: ServiceRequest, Service, Department
- Creates Neo4j relationships: FILED_FOR, HANDLED_BY
- Generates embeddings using sentence-transformers
- Stores embeddings in ChromaDB with metadata
- Handles duplicates with upsert logic

**Performance**: ~10-15 minutes for 10,000 records (GPU-accelerated)

### 2. Test Small Load

**Script**: `scripts/test_load_small.py`

Test with only 10 records before running full load.

```bash
source venv/bin/activate
python scripts/test_load_small.py
```

**Use this to**:
- Verify database connections
- Test loading functions
- Check data transformation
- Confirm GPU acceleration

### 3. Verify Data

**Script**: `scripts/verify_data.py`

Verify data was loaded successfully.

```bash
source venv/bin/activate
python scripts/verify_data.py
```

**Output**:
```
DATA LOAD VERIFICATION SUMMARY
============================================================

Neo4j Graph Database:
  • Service Requests: 3,811
  • Services: 5
  • Departments: 3

ChromaDB Vector Database:
  • Documents with Embeddings: 3,811

✅ Data load successful!
============================================================
```

---

## Database Schemas

### Neo4j Graph Schema

**Nodes**:
- `ServiceRequest`: Individual service requests with location, status, timestamps
- `Service`: Service types (e.g., "Streetlight Repair")
- `Department`: City departments (e.g., "Seattle City Light")

**Relationships**:
```cypher
(ServiceRequest)-[:FILED_FOR]->(Service)-[:HANDLED_BY]->(Department)
```

**Example Query**:
```cypher
MATCH (r:ServiceRequest)-[:FILED_FOR]->(s:Service)-[:HANDLED_BY]->(d:Department)
RETURN r, s, d LIMIT 25
```

### ChromaDB Vector Schema

**Collection**: `service-requests`

**Embeddings**:
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Processing: GPU-accelerated (CUDA) when available

**Metadata** (per document):
- service_type
- department
- location
- latitude, longitude
- status
- updated_date

**Document Format**:
```
Service: {service_type}. Department: {department}. Location: {location}.
Status: {status}. Details: {status_update}
```

---

## Implementation Details

### Data Flow

```
Seattle Open Data API
    ↓
Fetch & Transform (batches of 1000)
    ↓
    ├─→ Neo4j: Graph relationships
    │   └─ Services → Departments → Requests
    │
    └─→ ChromaDB: Vector embeddings
        └─ Semantic search ready
```

### Neo4j Loading (`load_to_neo4j`)

1. Extract unique services and departments
2. Create Service nodes (MERGE to avoid duplicates)
3. Create Department nodes
4. Create ServiceRequest nodes with properties
5. Create FILED_FOR relationships
6. Create HANDLED_BY relationships

### ChromaDB Loading (`load_to_chromadb`)

1. Generate searchable text from service data
2. Create embeddings using sentence-transformers
3. Store with rich metadata
4. Batch process 32 documents at a time
5. Use upsert to handle duplicates

### Duplicate Handling

- **Neo4j**: Uses `MERGE` to prevent duplicate nodes
- **ChromaDB**: Uses upsert to update existing records
- Safe to re-run scripts

---

## Exploring the Data

### Neo4j Browser

Visit: http://localhost:7474 (neo4j/testpassword123)

**Useful Queries**:

```cypher
// Count requests by service type
MATCH (s:Service)<-[:FILED_FOR]-(r:ServiceRequest)
RETURN s.name, count(r) as request_count
ORDER BY request_count DESC

// Find requests with locations
MATCH (r:ServiceRequest)
WHERE r.latitude IS NOT NULL
RETURN r.location, r.latitude, r.longitude LIMIT 10

// Explore department workload
MATCH (d:Department)<-[:HANDLED_BY]-(s:Service)<-[:FILED_FOR]-(r:ServiceRequest)
RETURN d.full_name, count(r) as total_requests
ORDER BY total_requests DESC

// Visualize graph structure
MATCH (r:ServiceRequest)-[:FILED_FOR]->(s:Service)-[:HANDLED_BY]->(d:Department)
RETURN r, s, d LIMIT 50
```

### ChromaDB Semantic Search

```python
import chromadb

# Connect
client = chromadb.HttpClient(host="localhost", port=8001)
collection = client.get_collection("service-requests")

# Count documents
print(f"Total documents: {collection.count()}")

# Search for similar requests
results = collection.query(
    query_texts=["broken streetlight on my street"],
    n_results=5
)

# Print results
for i, doc in enumerate(results['documents'][0]):
    print(f"\n{i+1}. ID: {results['ids'][0][i]}")
    print(f"   {doc}")
    print(f"   Distance: {results['distances'][0][i]}")
```

---

## Configuration

All settings in `.env`:

```bash
# Seattle Open Data API
SEATTLE_DATA_API=https://data.seattle.gov/resource/43nw-pkdq.json
SEATTLE_DATA_APP_TOKEN=  # Optional, not required for this endpoint

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpassword123
NEO4J_DATABASE=neo4j

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION=service-requests

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Performance Expectations

**For 10,000 records**:
- Fetch time: 1-2 minutes
- Neo4j loading: 3-5 minutes
- ChromaDB embedding generation: 5-8 minutes (with GPU)
- **Total: 10-15 minutes**

**Hardware Acceleration**:
- GPU (CUDA) automatically used for embeddings if available
- CPU fallback is automatic but slower
- Check logs for "cuda:0" to confirm GPU usage

---

## Troubleshooting

### Issue: Connection Errors

**Solution**: Verify databases are running
```bash
docker compose ps
docker compose logs neo4j
docker compose logs chromadb
```

### Issue: Slow Embedding Generation

**Solution**: Verify GPU usage
- Check logs for "cuda:0" (GPU) vs "cpu" (slower)
- Reduce batch size if running out of memory

### Issue: Duplicate Key Errors

**Solution**: Already handled with upsert logic
- Re-running is safe
- Will update existing records

### Issue: Memory Errors

**Solution**: Reduce batch size
```python
# In scripts/load_data.py
batch_size = 500  # Default is 1000
```

### Issue: API Rate Limiting

**Solution**: Add app token
1. Sign up at https://data.seattle.gov
2. Create API token in Developer Settings
3. Add to `.env`: `SEATTLE_DATA_APP_TOKEN=your_token`

---

## Reloading Data

To reload or refresh data:

```bash
# 1. Clear Neo4j (optional)
# In Neo4j Browser: MATCH (n) DETACH DELETE n

# 2. Clear ChromaDB (optional)
# Delete and recreate collection

# 3. Reload
source venv/bin/activate
python scripts/load_data.py
```

---

## Next Steps After Loading

With data loaded, you can now:

### 1. Implement GraphRAG Services
- **Vector Search Service**: Query ChromaDB for similar requests
- **Graph Query Service**: Find patterns in Neo4j
- **GraphRAG Orchestrator**: Combine both for hybrid search

### 2. Build LLM Triage Service
- Use retrieved context for classification
- Provide reasoning based on historical data

### 3. Train ML Models
```bash
source venv/bin/activate
python ml/training/train_models.py
```

### 4. Test the API Pipeline
```bash
cd services/api-gateway
python main.py

# Then test:
curl -X POST http://localhost:8000/api/v2/triage \
  -H "Content-Type: application/json" \
  -d '{"text": "broken streetlight on 5th avenue"}'
```

---

## Data Quality Notes

### Why 3,811 records (not 10,000)?

The script attempted to load 10,000 records, but:
- Some records lacked valid IDs
- Duplicates were filtered
- Result: 3,811 **unique, valid** service requests

This is an excellent dataset for the MVP!

### Data Completeness

**Fields Loaded**:
- ✅ Service request numbers (unique IDs)
- ✅ Service types and departments
- ✅ Locations with coordinates
- ✅ Status information and updates
- ✅ Timestamp data
- ✅ Graph relationships
- ✅ Semantic embeddings

---

## Support

- **Database Issues**: Run `scripts/verify_data.py`
- **API Issues**: Check Seattle Open Data status page
- **Memory Issues**: Reduce batch size in loading scripts
- **General Help**: See [CLAUDE.md](CLAUDE.md) for architecture details

---

**Last Updated**: 2025-11-06
**Data Version**: 3,811 Seattle service requests
**Status**: ✅ Loaded and verified
