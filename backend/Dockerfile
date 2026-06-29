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

# Run — apply any pending DB migrations, then start the server.
# `alembic upgrade head` is idempotent (no-op when already at head); running it
# on every boot keeps the live schema in lockstep with the ORM models so new
# columns never 500 the API after a deploy. Soft-fail (|| echo) so a migration
# hiccup doesn't take the whole service offline; `exec` hands signals to uvicorn.
# Single worker is fine for the Render free tier.
CMD ["sh", "-c", "alembic upgrade head || echo 'WARNING: alembic upgrade head failed; starting anyway'; exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1"]
