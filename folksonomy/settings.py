import os

# Postgres
POSTGRES_USER = os.environ.get(
    "POSTGRES_USER", None
)  # Leave empty if no user exists for database
POSTGRES_PASSWORD = os.environ.get(
    "POSTGRES_PASSWORD", None
)  # Leave empty if no password exists for user
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", None)  # Change if necessary
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE", "folksonomy")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", 5432)


# The authentication server (a Product Opener instance) against which
# credentials are checked. It must only ever come from server-side
# configuration: deriving it from the request (e.g. from the Host header)
# would let any caller redirect credentials to a server they control and
# have the roles that server asserts (admin / moderator) trusted.
AUTH_SERVER = os.environ.get("AUTH_SERVER", "https://world.openfoodfacts.org")

# OpenAPI server configuration
API_SERVERS = [
    {
        "url": os.environ.get(
            "API_SERVER_URL", "https://api.folksonomy.openfoodfacts.org"
        ),
        "description": os.environ.get("API_SERVER_DESCRIPTION", "Production server"),
    },
    {"url": "http://localhost:8000", "description": "Local development server"},
]

# time (in seconds) to wait for after a failed authentication attempt (to avoid brute force)
FAILED_AUTH_WAIT_TIME = 2  # this settings is meant to be overridden by tests only

try:
    # override with local_settings
    from local_settings import *  # noqa: F403
except ImportError:
    pass
