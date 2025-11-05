FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Copy application code
COPY services/graphrag-orchestrator /app
COPY services/vector-search /services/vector-search
COPY services/graph-query /services/graph-query
COPY shared /shared

# Run application
CMD ["python", "main.py"]
