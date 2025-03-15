# OpenFoodFacts username and password for authentication for tests only!
OFF_TEST_USER = 'myusername'
OFF_TEST_PASSWORD = 'mypassword'

# Postgres
POSTGRES_USER = '' # Leave empty if no user exists for database
POSTGRES_PASSWORD = '' # Leave empty if no password exists for user
POSTGRES_HOST = '127.0.0.1' # Change if necessary
POSTGRES_DATABASE = 'folksonomy'

# for dev using a local product opener instance you can use this
# base domain has to be the same (see INSTALL.md)
#FOLKSONOMY_PREFIX="api.folksonomy.openfoodfacts.localhost:8888"
#AUTH_PREFIX="world.openfoodfacts.localhost"

# For dev, use this setting if you want to test without installing Product 
# Opener locally, and using an external website as an auth server.
# Eg. AUTH_SERVER_STATIC="https://world.openfoodfacts.org"
#AUTH_SERVER_STATIC="https://world.openfoodfacts.org"