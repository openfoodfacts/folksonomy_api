"""Simple db migrations script to apply all pending yoyo migrations

In case you need, you can also use the command line. Eg to list migrations:
```bash
yoyo -c yoyo.ini --database postgres://you_database_url list
```

This can be usefull to mark a migration as already applied without actually applying it.
eg:
```bash
yoyo -c yoyo.ini --database postgres://you_database_url mark
```
"""
import os
import time

from yoyo import read_migrations, get_backend

from folksonomy.settings import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DATABASE

AUTH_DATA = ""
if POSTGRES_USER:
    AUTH_DATA += POSTGRES_USER
    if POSTGRES_PASSWORD:
        AUTH_DATA += ":" + POSTGRES_PASSWORD
if AUTH_DATA:
    AUTH_DATA += "@"

url = "postgres://{}{}/{}".format(AUTH_DATA, POSTGRES_HOST or "", POSTGRES_DATABASE)
backend = get_backend(url)
print(f"Going to connect to {url}")

# Add steps
migrations = read_migrations('./db/migrations')

# Apply any outstanding migrations
to_apply = backend.to_apply(migrations)
print(f"Found {len(to_apply)} migrations to apply")
if to_apply:
    start = time.monotonic()
    backend.apply_migrations(to_apply)
    end = time.monotonic()
    print(f"Done in {end - start:.2} seconds")
