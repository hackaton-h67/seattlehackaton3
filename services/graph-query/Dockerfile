FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Copy application code
COPY services/graph-query /app
COPY shared /shared

# Run application
CMD ["python", "main.py"]
