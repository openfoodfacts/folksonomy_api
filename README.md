# Folksonomy API
A light REST API designed for the Open Food Facts Folksonomy Engine.

* Design documents: https://wiki.openfoodfacts.org/Folksonomy_Engine
* API endpoint: https://api.folksonomy.openfoodfacts.org/
* API Documentation with interactive "try-out": https://api.folksonomy.openfoodfacts.org/docs
* Browser extension to try it live: https://github.com/openfoodfacts/folksonomy_frontend
* Moderators can access it on Open Food Facts without any extension. The UI has not yet been deployed on Open Products Facts, Open Pet Food Facts or Open Beauty Facts, but has been proven to work, thanks to the extension


# Contributor's guide

Check our [contributor's guide](./CONTRIBUTING.md). Don't hesitate to improve it or ask questions.

# Dependencies

The code is written in Python 3.x and uses [FastAPI](https://fastapi.tiangolo.com/) framework.

PostgreSQL is used as the backend database.

# Dev

You should create unit tests for each new feature or API change (see [test_main.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/tests/test_main.py)). 
To run tests just launch:
```bash
PYTHONASYNCIODEBUG=1 pytest tests/ folksonomy/
```
The `PYTHONASYNCIODEBUG` is important to check we have no pending asyncio tasks that are not executed
(sign of a potential problem).

Please note that running tests empties the database. DO NOT RUN TESTS in production.

# Docker Setup 

An easy way to get started with Folksonomy API is to use Docker (if you don't mind using it). This approach requires minimal setup and provides a consistent development environment.

## Requirements
- Docker 17.06.0+
- Docker Compose 1.21.0+

## Quick Start
```markdown
1. Clone the repository
   ```bash
   git clone https://github.com/openfoodfacts/folksonomy_api.git
   cd folksonomy_api
   ```

2. Copy the example settings file for Docker
   ```bash
   cp local_settings_docker_example.py local_settings.py
   ```

3. Create an environment configuration file
   ```bash
   cp .env.example .env
   ```

4. Start the services
   ```bash
   docker compose up -d
   ```

5. Initialize the database (necessary on first run)
   ```bash
   docker compose exec api python db-migration.py
   ```

6. Access the API
   - API: http://localhost:8000
   - Interactive documentation: http://localhost:8000/docs

7. Stop the services
   ```bash
   docker compose down
   ```
```


## Configuration

The Docker setup uses environment variables defined in the `docker-compose.yml` file. You can modify these as needed:

- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password  
- `POSTGRES_DATABASE`: Database name
- `POSTGRES_HOST`: Database host (default: db)

You can also modify additional settings in the `local_settings.py` file to configure authentication and other application parameters.

Note: The port is 5433 to avoid conflicts with any local PostgreSQL installations.

## Working with the Database

To connect to the PostgreSQL database in the Docker container:

```bash
docker compose exec db psql -U folksonomy -d folksonomy
```


# Traditional Setup

If you prefer to install directly on your machine without Docker:

1. Install Python 3.8+
2. Install pip
3. Install PostgreSQL 13+
4. Follow the steps in [INSTALL.md](https://github.com/openfoodfacts/folksonomy_api/blob/main/INSTALL.md) to install requirements and for creating a db user
5. Make a copy of [local_settings_example.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/local_settings_example.py) and rename it to *local_settings.py*
6. Change parameters accordingly in *local_settings.py*
7. That's all!

# Generating an OpenAPI document

FastAPI is based on [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (previously known as Swagger) and [JSON Schema](https://json-schema.org/). FastAPI allows to generate an OpenAPI document (JSON) that you can reuse in various services (to automatically generate client libraries for example). To generate an OpenAPI document you can either:
* download it at https://api.folksonomy.openfoodfacts.org/openapi.json
* or generate it:
```bash
./generate_openapi_json.py
```

When running in Docker, use:
```bash
docker compose exec api python generate_openapi_json.py
```

## Deployment

[Deployment at Open Food Facts - Folksonomy Section](https://openfoodfacts.github.io/openfoodfacts-infrastructure/folksonomy/)