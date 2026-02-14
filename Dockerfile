# --- uv image ---
ARG UV_VERSION=0.10.2
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# --- Base Stage ---
FROM python:3.11-slim AS base

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
  curl \
  && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -U folksonomy

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
  POSTGRES_HOST=${POSTGRES_HOST}

# virtual environment
COPY --from=builder /app/ /app/
# application code
COPY . .
# entrypoint and healthcheck scripts
COPY ./docker/entrypoint.sh /app/start.sh
COPY ./docker/healthcheck.sh /app/healthcheck.sh

# Fix permissions
RUN mkdir -p /app/logs && \
  chown -R folksonomy:folksonomy /app && \
  chmod +x /app/start.sh

USER folksonomy

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD ["/app/healthcheck.sh"]
CMD ["/app/start.sh"]
