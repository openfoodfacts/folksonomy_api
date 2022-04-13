from yoyo import read_migrations, get_backend
from local_settings import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST

# Check if Postgres User has a password 
if (POSTGRES_PASSWORD):
    url = "postgres://{}:{}@{}/folksonomy".format(POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST)
else:
    url = "postgres://{}@{}/folksonomy".format(POSTGRES_USER, POSTGRES_HOST)

backend = get_backend(url)
# Add steps
migrations = read_migrations('./db/migrations')

# Apply any outstanding migrations
backend.apply_migrations(backend.to_apply(migrations))