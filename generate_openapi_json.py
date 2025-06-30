#! /bin/env python3

import json
import sys
import os

# Mock the database dependencies for OpenAPI generation when DB is not available
try:
    import psycopg2
except ImportError:
    sys.modules['psycopg2'] = type(sys)('psycopg2')

try:
    import aiopg
except ImportError:
    sys.modules['aiopg'] = type(sys)('aiopg')

# Mock the database module to avoid connection errors during OpenAPI generation
if 'folksonomy.db' not in sys.modules:
    import types
    db_mock = types.ModuleType('db')
    sys.modules['folksonomy.db'] = db_mock

from folksonomy.api import app

# Generate and format the OpenAPI JSON with proper indentation
openapi_spec = app.openapi()
json.dump(openapi_spec, sys.stdout, indent=2, ensure_ascii=False)