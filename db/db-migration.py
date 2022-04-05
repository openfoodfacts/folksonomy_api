from yoyo import read_migrations, get_backend
from db_settings import postgresUser, postgresHost

url = "postgres://{}@{}/folksonomy".format(postgresUser, postgresHost)
backend = get_backend(url)
migrations = read_migrations('./migrations')

# Apply any outstanding migrations
backend.apply_migrations(backend.to_apply(migrations))
