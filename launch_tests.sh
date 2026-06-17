#!/usr/bin/env bash

# export some variables as environment variables
export PYTHONASYNCIODEBUG=1
export POSTGRES_DATABASE=test_folksonomy
# Create test database
docker exec -i -u postgres fe_postgres psql -U folksonomy folksonomy <<-EOSQL
    DROP DATABASE IF EXISTS test_folksonomy;
	CREATE DATABASE test_folksonomy;
	GRANT ALL PRIVILEGES ON DATABASE test_folksonomy TO folksonomy;
EOSQL
#read -p "Press [Enter] key to continue..."
python ./db-migration.py
pytest tests/ #folksonomy/
