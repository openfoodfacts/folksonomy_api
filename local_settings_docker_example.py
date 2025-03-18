import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =====================================================================
# DATABASE CONFIGURATION
# =====================================================================

# PostgreSQL connection settings
# Retrieve from environment variables with sensible defaults
POSTGRES_USER = os.getenv('POSTGRES_USER', 'folksonomy')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'folksonomy')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'folksonomy')

# =====================================================================
# AUTHENTICATION CONFIGURATION
# =====================================================================

# FOLKSONOMY_PREFIX - allows configuration via environment
FOLKSONOMY_PREFIX = os.getenv('FOLKSONOMY_PREFIX', 'api.folksonomy')

# AUTH_PREFIX - allows configuration via environment
AUTH_PREFIX = os.getenv('AUTH_PREFIX', 'world')

# Optional static authentication server URL
# Use environment variable, fallback to None if not set
AUTH_SERVER_STATIC = os.getenv('AUTH_SERVER_STATIC')

# =====================================================================
# SECURITY SETTINGS
# =====================================================================

# Failed authentication wait time - configurable via environment
FAILED_AUTH_WAIT_TIME = int(os.getenv('FAILED_AUTH_WAIT_TIME', '2'))

# =====================================================================
# TEST SETTINGS
# =====================================================================

# Test user credentials from environment
OFF_TEST_USER = os.getenv('OFF_TEST_USER', '')
OFF_TEST_PASSWORD = os.getenv('OFF_TEST_PASSWORD', '')

# Determine runtime environment
IS_PRODUCTION = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
IS_TESTING = os.getenv('ENVIRONMENT', 'development').lower() == 'testing'

# Additional environment-based configuration
DEBUG = not IS_PRODUCTION

# Logging configuration
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')