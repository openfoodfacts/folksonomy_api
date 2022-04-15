import os
from yoyo import read_migrations, get_backend
from local_settings import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST

AUTH_DATA = ""
if POSTGRES_USER:
    AUTH_DATA += POSTGRES_USER
    if POSTGRES_PASSWORD:
        AUTH_DATA += ":" + POSTGRES_PASSWORD
if AUTH_DATA:
    AUTH_DATA += "@"

url = "postgres://{}{}/folksonomy".format(AUTH_DATA, POSTGRES_HOST)
backend = get_backend(url)

# Add steps
migrations = read_migrations('./db/migrations')

# Apply any outstanding migrations
backend.apply_migrations(backend.to_apply(migrations))