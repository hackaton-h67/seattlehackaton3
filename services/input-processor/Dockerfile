FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Copy application code
COPY services/input-processor /app
COPY shared /shared

# Run application
CMD ["python", "main.py"]
