# Folksonomy API

A lightweight REST API designed for the Open Food Facts Folksonomy Engine.

- **Design documents**: [Folksonomy Engine Wiki](https://wiki.openfoodfacts.org/Folksonomy_Engine)
- **API endpoint**: [https://api.folksonomy.openfoodfacts.org/](https://api.folksonomy.openfoodfacts.org/)
- **Interactive API documentation**: [https://api.folksonomy.openfoodfacts.org/docs](https://api.folksonomy.openfoodfacts.org/docs)
- **Browser extension to try it live**: [folksonomy_frontend GitHub](https://github.com/openfoodfacts/folksonomy_frontend)
- **Note**: Moderators can access the folksonomy engine directly on Open Food Facts without any extension.
  The UI has not yet been deployed on Open Products Facts, Open Pet Food Facts, or Open Beauty Facts, but it has been proven to work via the extension.

# Contributor's Guide

Check out our [Contributor's Guide](./CONTRIBUTING.md).
Feel free to improve it or ask questions!

# Dependencies

- **Language**: Python 3.x
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: PostgreSQL

# Development

You should create unit tests for each new feature or API change (see [test_main.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/tests/test_main.py)).

To run tests, simply launch:

```bash
PYTHONASYNCIODEBUG=1 pytest tests/ folksonomy/
```

- The `PYTHONASYNCIODEBUG=1` environment variable is important to ensure there are no pending asyncio tasks (a sign of potential issues).
- **Warning**: Running tests will wipe the database. **Do not run tests in production.**

# Docker Setup

Using Docker is the easiest way to get started with the Folksonomy API.
It requires minimal setup and ensures a consistent development environment.

## Requirements

- Docker 17.06.0+
- Docker Compose 1.21.0+

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/openfoodfacts/folksonomy_api.git
   cd folksonomy_api
   ```

2. Copy the example settings file:
   ```bash
   cp local_settings_docker_example.py local_settings.py
   ```

3. Create an environment configuration file:
   ```bash
   cp .env.example .env
   ```

3. Eventually create the shared network (it might already exist if you develop with [openfoodfacts-server](https://github.com/openfoodfacts/openfoodfacts-server/pulls))
   ```bash
   docker network create po_default
   ```

4. Start the services:
   ```bash
   docker compose up -d
   ```

5. Initialize the database (necessary on the first run or after migrations):
   ```bash
   docker compose run --rm folksonomy_api python db-migration.py
   ```

6. Access the API:
   - API: [http://localhost:8000](http://localhost:8000)
   - Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

7. Stop the services:
   ```bash
   docker compose down
   ```

### Development with Product Opener (Open Food Facts server)

If you want to test the integration with the Open Food Facts server,
you just have to edit your .env to set:
```conf
AUTH_SERVER_STATIC=http://world.openfoodfacts.localhost
```
Then run your server and also run folksonomy_api.

Change your local openfoodfacts-server instance to use your local folksonomy_api instance, which is at folksonomy_api:8000.
**TODO:** document how

## Configuration

The Docker setup uses environment variables defined in `docker-compose.yml`.
You can modify these as needed:

- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DATABASE`: Database name
- `POSTGRES_HOST`: Database host (default: `db`)

Additional settings (such as authentication) can be configured in `local_settings.py`.

**Note**: The PostgreSQL service uses port `5433` to avoid conflicts with any local PostgreSQL installations.

## Working with the Database

To connect to the PostgreSQL database inside the Docker container:

```bash
docker compose exec db psql -U folksonomy -d folksonomy
```

# Traditional Setup

If you prefer installing everything directly on your machine (without Docker):

1. Install Python 3.9+
2. Install Poetry
3. Install PostgreSQL 13+
4. Follow the instructions in [INSTALL.md](https://github.com/openfoodfacts/folksonomy_api/blob/main/INSTALL.md) to install the requirements and create a database user.
5. Copy [local_settings_example.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/local_settings_example.py) and rename it to `local_settings.py`.
6. Update the parameters in `local_settings.py` as needed.
7. That's it!

# Generating an OpenAPI Document

FastAPI uses [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (formerly Swagger) and [JSON Schema](https://json-schema.org/).

You can generate the OpenAPI JSON document in two ways:

- Download it from [https://api.folksonomy.openfoodfacts.org/openapi.json](https://api.folksonomy.openfoodfacts.org/openapi.json)
- Or generate it locally:

```bash
./generate_openapi_json.py
```

If running inside Docker:

```bash
docker compose exec api python generate_openapi_json.py
```

## Testing Product Opener integration (with docker)

To test with product opener, you just need to run the [openfoodfacts-server project]() and the folksonomy_api project using docker compose.

Thanks to the use a common_net (a common docker network),
the openfoodfacts server will be able to communicate with the folksonomy_api docker,
and the nginx frontend of openfoodfacts-server will act as a proxy to your folksonomy_api server
(see `conf/nginx-docker/nginx.conf`).

After both projects are fully launched,
you should be able to address http://api.folksonomy.openfoodfacts.localhost
to access the folksonomy_api server (without using a specific port).

In case you are not sure about network names and so on,
using `docker inspect <containenr-name>` and
`docker network inspect <network-name>` can help you.

# Code Style

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting.

- We recommend using pre-commit hooks for automatic linting, but it's optional (see [install](https://pre-commit.com/#install)).
- See [CONTRIBUTING.md](CONTRIBUTING.md) for more details on code style and linting.


# Deployment

Deployment information is available here:
[Open Food Facts - Folksonomy Deployment](https://openfoodfacts.github.io/openfoodfacts-infrastructure/folksonomy/)
