# folksonomy_api
A light REST API designed for Open Food Facts folksonomy engine.

Design documents: https://wiki.openfoodfacts.org/Folksonomy_Engine

API endpoint: https://api.folksonomy.openfoodfacts.org/

API Documentation with interactive "try-out": https://api.folksonomy.openfoodfacts.org/docs

Browser extension to try it live: https://github.com/openfoodfacts/folksonomy_frontend

# Dependencies

The code is written in python 3.x and uses [FastAPI](https://fastapi.tiangolo.com/) framework.

Postgresql is used as the backend database.

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
3. pip install -r requirements.txt
4. Install postgre
5. Create a user
6. XXX
