FROM python:3.12-slim

WORKDIR /app

# System deps — build tools for chromadb, psycopg native driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Chroma persistent directory (ephemeral in free tier — OK for demo)
RUN mkdir -p /app/chroma_data

# Port
EXPOSE 8000

# Run — single worker is fine for Render free tier
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
