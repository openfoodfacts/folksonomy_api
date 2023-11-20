# Postgres
POSTGRES_USER = None # Leave empty if no user exists for database
POSTGRES_PASSWORD = None # Leave empty if no password exists for user
POSTGRES_HOST = None # Change if necessary
POSTGRES_DATABASE = 'folksonomy'

try:
    # override with local_settings
    from local_settings import *
except ImportError:
    pass