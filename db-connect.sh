#!/bin/bash
# db-connect.sh - Connect to the PostgreSQL database


# Connect to PostgreSQL using environment variables
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DATABASE "$@"