# Folksonomy API
A light REST API designed for the Open Food Facts Folksonomy Engine.

* Design documents: https://wiki.openfoodfacts.org/Folksonomy_Engine
* API endpoint: https://api.folksonomy.openfoodfacts.org/
* API Documentation with interactive "try-out": https://api.folksonomy.openfoodfacts.org/docs
* Browser extension to try it live: https://github.com/openfoodfacts/folksonomy_frontend
* Moderators can access it on Open Food Facts without any extension. The UI has not yet been deployed on Open Products Facts, Open Pet Food Facts or Open Beauty Facts, but has been proven to work, thanks to the extension

# Dependencies

The code is written in Python 3.x and uses [FastAPI](https://fastapi.tiangolo.com/) framework.

PostgreSQL is used as the backend database.

# Dev

You should create unit tests for each new feature or API change (see [test_main.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/tests/test_main.py)). 
To run tests just launch:
```bash
pytest
```

# Generating an OpenAPI document

FastAPI is based on [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (previously known as Swagger) and [JSON Schema](https://json-schema.org/). FastAPI allows to generate an OpenAPI document (JSON) that you can reuse in various services (to automatically generate client libraries for example). To generate an OpenAPI document you can either:
* download it at https://api.folksonomy.openfoodfacts.org/openapi.json 
* or generate it:
```bash
./generate_openapi_json.py
```

# How to install Folksonomy Engine on your local machine

1. Install Python 3.8+
2. Install pip
3. Install PostgreSQL 13+
4. Follow the steps in [INSTALL.md](https://github.com/openfoodfacts/folksonomy_api/blob/main/INSTALL.md) to install requirements and for creating a db user
5. Make a copy of [local_settings_example.py](https://github.com/openfoodfacts/folksonomy_api/blob/main/local_settings_example.py) and remame it to *local_settings.py*
6. Change parameters accordingly in *local_settings.py*
7. That's all!
