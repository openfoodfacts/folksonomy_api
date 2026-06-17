# --- Base Stage ---
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH"

# --- Builder Stage ---
FROM base AS builder

# Poetry installation variables
ARG POETRY_VERSION=2.0.1
ARG POETRY_HOME="/opt/poetry"

# Build environment variables
ENV PIP_NO_CACHE_DIR=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_NO_INTERACTION=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

# 1. Install Poetry in its own isolated venv via pip
RUN python -m venv ${POETRY_HOME} && \
  ${POETRY_HOME}/bin/pip install --upgrade pip && \
  ${POETRY_HOME}/bin/pip install poetry==${POETRY_VERSION}

# Add Poetry's isolated venv to the PATH for the builder stage
ENV PATH="${POETRY_HOME}/bin:$PATH"

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml poetry.lock* ./

# 2. Install app dependencies into /app/.venv
RUN poetry install --no-root --only main

# --- Runtime Stage ---
FROM base AS runtime

# Install runtime-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq5 \
  netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -U folksonomy

WORKDIR /app

# Copy the app's virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application source code
COPY . .

# --- GENERATE START SCRIPT ---
RUN tee /app/start.sh <<-'EOF'
#!/bin/bash
while ! nc -z "$POSTGRES_HOST" 5432; do
  echo "Waiting for PostgreSQL at $POSTGRES_HOST..."
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Starting Folksonomy API server..."
gunicorn folksonomy.api:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
EOF

# Fix permissions
RUN mkdir -p /app/logs && \
  chown -R folksonomy:folksonomy /app && \
  chmod +x /app/start.sh

USER folksonomy

EXPOSE 8000

CMD ["/app/start.sh"]
