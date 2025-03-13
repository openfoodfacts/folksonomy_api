# EXAMPLE CONFIGURATION FILE FOR FOLKSONOMY API
# Copy this file to local_settings.py and adjust the settings as needed

# =====================================================================
# DATABASE CONFIGURATION
# =====================================================================

# PostgreSQL connection settings
# These will be used to connect to your PostgreSQL database
POSTGRES_USER = 'folksonomy'  # Database username
POSTGRES_PASSWORD = 'folksonomy'  # Database password
POSTGRES_HOST = '127.0.0.1'  # Database host (use 'db' for Docker setup)
POSTGRES_DATABASE = 'folksonomy'  # Database name

# =====================================================================
# AUTHENTICATION CONFIGURATION
# =====================================================================

# FOLKSONOMY_PREFIX is used to identify the domain/subdomain where the 
# Folksonomy API is running
# For production: "api.folksonomy"
# For local dev with local Product Opener: "api.folksonomy.openfoodfacts.localhost:8888"
FOLKSONOMY_PREFIX = "api.folksonomy"

# AUTH_PREFIX is used to identify the domain/subdomain where the
# authentication server (Product Opener) is running
# For production: "world"
# For local dev with local Product Opener: "world.openfoodfacts.localhost"
AUTH_PREFIX = "world"

# AUTH_SERVER_STATIC can be used to specify a static authentication server URL
# This overrides the automatically calculated URL from PREFIX settings
# Only use this for development/testing
# Example: "https://world.openfoodfacts.org"
# Set to None or comment out to use the PREFIX-based authentication
# AUTH_SERVER_STATIC = "https://world.openfoodfacts.org"

# =====================================================================
# SECURITY SETTINGS
# =====================================================================

# Time in seconds to wait after a failed authentication attempt
# This helps prevent brute force attacks
FAILED_AUTH_WAIT_TIME = 2

# =====================================================================
# TEST SETTINGS
# =====================================================================

# Test user credentials for running tests
# These are only used in the test environment
# DO NOT use real production credentials here
OFF_TEST_USER = ''  # Your Open Food Facts username for testing
OFF_TEST_PASSWORD = ''  # Your Open Food Facts password for testing

# =====================================================================
# DEVELOPMENT SCENARIOS
# =====================================================================

# SCENARIO 1: USING DOCKER
# If you're using Docker, use these settings:
# POSTGRES_USER = 'folksonomy'
# POSTGRES_PASSWORD = 'folksonomy'
# POSTGRES_HOST = 'db'
# POSTGRES_DATABASE = 'folksonomy'
# AUTH_SERVER_STATIC = "https://world.openfoodfacts.org"

# SCENARIO 2: LOCAL DEV WITH LOCAL PRODUCT OPENER
# If you're running a local Product Opener instance and want to authenticate against it:
# POSTGRES_USER = 'folksonomy'
# POSTGRES_PASSWORD = 'folksonomy' 
# POSTGRES_HOST = '127.0.0.1'
# POSTGRES_DATABASE = 'folksonomy'
# FOLKSONOMY_PREFIX = "api.folksonomy.openfoodfacts.localhost:8888"
# AUTH_PREFIX = "world.openfoodfacts.localhost"
# Comment out AUTH_SERVER_STATIC if it's defined

# SCENARIO 3: LOCAL DEV WITHOUT PRODUCT OPENER
# If you're developing locally without a Product Opener instance:
# POSTGRES_USER = 'folksonomy'
# POSTGRES_PASSWORD = 'folksonomy'
# POSTGRES_HOST = '127.0.0.1'
# POSTGRES_DATABASE = 'folksonomy'
# AUTH_SERVER_STATIC = "https://world.openfoodfacts.org"