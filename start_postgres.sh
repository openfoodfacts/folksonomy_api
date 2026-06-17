#!/usr/bin/env bash
#
# data
mkdir -p data/pg
echo "🤓 starting postgresql container (use it only for dev !)"
echo ""
echo "🤓 to psql inside, use: docker exec -ti -u postgres fe_postgres psql -U folksonomy folksonomy"
echo ""
docker run --name fe_postgres \
    -v $(realpath $(dirname $0))/data/pg:/var/lib/postgresql/data \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -p 127.0.0.1:5432:5432 \
    -e POSTGRES_HOST_AUTH_METHOD=trust \
    -e POSTGRES_USER=folksonomy \
    -e POSTGRES_PASSWORD=folksonomy \
    -e POSTGRES_DB=folksonomy \
    --rm postgres:13
