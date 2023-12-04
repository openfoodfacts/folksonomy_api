import os

# Postgres
POSTGRES_USER = os.environ.get("POSTGRES_USER", None) # Leave empty if no user exists for database
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", None) # Leave empty if no password exists for user
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", None) # Change if necessary
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE", 'folksonomy')


# If you're in dev, you can specify another auth_server; eg.
#   AUTH_URL="http://localhost.openfoodfacts" uvicorn folksonomy.api:app --host
# Otherwise it defaults to https://world.openfoodfacts.org
AUTH_SERVER = os.environ.get("AUTH_URL", "https://world.openfoodfacts.org")

# time (in seconds) to wait for after a failed authentication attempt (to avoid brute force)
FAILED_AUTH_WAIT_TIME = 2  # this settings is meant to be overridden by tests only

try:
    # override with local_settings
    from local_settings import *
except ImportError:
    pass
