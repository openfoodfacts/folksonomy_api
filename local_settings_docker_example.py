import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =====================================================================
# DATABASE CONFIGURATION
# =====================================================================

# PostgreSQL connection settings
# Retrieve from environment variables with sensible defaults
POSTGRES_USER = os.getenv("POSTGRES_USER", "folksonomy")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "folksonomy")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "folksonomy_db")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "folksonomy")

# =====================================================================
# AUTHENTICATION CONFIGURATION
# =====================================================================

# AUTH_SERVER - the authentication server URL, via environment
AUTH_SERVER = os.getenv("AUTH_SERVER", "https://world.openfoodfacts.org")

# Optional static authentication server URL
# Use environment variable, fallback to None if not set
AUTH_SERVER_STATIC = os.getenv("AUTH_SERVER_STATIC")

# =====================================================================
# SECURITY SETTINGS
# =====================================================================

# Failed authentication wait time - configurable via environment
FAILED_AUTH_WAIT_TIME = int(os.getenv("FAILED_AUTH_WAIT_TIME", "2"))

# =====================================================================
# TEST SETTINGS
# =====================================================================

# TO BE IMPLEMENTED IN FUTURE
