from yoyo import read_migrations, get_backend

# Change user and host as per requirement
user = "aadarsh"
host = "localhost"

url = "postgres://{}@{}/folksonomy".format(user, host)
backend = get_backend(url)
migrations = read_migrations('./migrations')

# Apply any outstanding migrations
backend.apply_migrations(backend.to_apply(migrations))
