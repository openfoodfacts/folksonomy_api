ARG UV_VERSION=0.12.23
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# --- Base Stage ---
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  VIRTUAL_ENV=/app/.venv \
  PATH="/app/.venv/bin:$PATH"

# --- Builder Stage ---
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# --- Runtime Stage ---
FROM base AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
  libpq5 \
  netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -m -U folksonomy

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

RUN tee /app/start.sh <<-'EOF'
#!/bin/bash
while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
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

RUN mkdir -p /app/logs && \
  chown -R folksonomy:folksonomy /app && \
  chmod +x /app/start.sh

USER folksonomy
EXPOSE 8000
CMD ["/app/start.sh"]
