# --- uv image ---
ARG UV_VERSION=0.10.2
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# --- Base Stage ---
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH"

# --- Builder Stage ---
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock* ./

# 2. Install app dependencies into /app/.venv
RUN uv sync --locked --no-dev --no-install-project

COPY README.md LICENSE ./
COPY ./src ./src

RUN uv sync --locked --no-dev

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
