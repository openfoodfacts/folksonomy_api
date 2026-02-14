#!/bin/bash

set -e

# 1. Wait for DB
while ! nc -z "$POSTGRES_HOST" 5432; do
  echo "Waiting for PostgreSQL at $POSTGRES_HOST..."
  sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
# 2. Run Yoyo migrations
# Replace 'migrations' with your folder name and 'postgresql://...' with your env var
DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
yoyo apply -vv --batch --database $DATABASE_URL ./db/migrations/

echo "Starting application..."
# 3. Start the application
exec uvicorn off_folksonomy.api:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8000
