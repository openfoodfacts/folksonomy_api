from yoyo import read_migrations, get_backend
from local_settings import postgresUser, postgresHost

url = "postgres://{}@{}/folksonomy".format(postgresUser, postgresHost)
backend = get_backend(url)
# Add steps
migrations = read_migrations('./db/migrations')

# Apply any outstanding migrations
backend.apply_migrations(backend.to_apply(migrations))