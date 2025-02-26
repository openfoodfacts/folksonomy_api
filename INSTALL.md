# HOWTO install/test Folksonomy API

## Requirements

- Postgresql 13 (lower version may be OK, but untested)
- Python 3.8 (lower version may be ok too, but untested)
- Python modules in "requirements.txt"

## Setup

```
# clone repo
git clone https://github.com/openfoodfacts/folksonomy_api.git
cd folksonomy_api

# required packages to setup a virtualenv (optional, but recommended)
apt install python3-virtualenv virtualenv virtualenvwrapper

# create and switch to virtualenv
# if mkvirtualenv command is not found, search for virtualenvwrapper.sh 
# (/usr/share/virtualenvwrapper/virtualenvwrapper.sh, or /usr/bin/virtualenvwrapper.sh, for example)
# add the path in your bash profile
mkvirtualenv folksonomy -p /usr/bin/python3
workon folksonomy

# install 
pip install -r requirements.txt
```
If you install PostgreSQL yourself, here is how to set it up:
```bash
# create dbuser if needed
sudo -u postgres createuser $USER

# create Postgresql database if needed
sudo -u postgres createdb folksonomy -O $USER
psql folksonomy < db/db_setup.sql
```
Otherwise, you can use the `./start_postgres.sh` which launch a ready to use Postgres Docker container. You don't have to install Postgres but you need to have Docker installed. Here are some tips to use it:
```bash
# launch Postgres Docker container
./start_postgres.sh # Have a look at the log messages

# you can also launch it in the background
./start_postgres.sh & # but log messages are not displayed anymore

# if you have launched the container in the background, stop the container like this:
docker stop fe_postgres

# if you want to use psql inside the Docker container:
docker exec -ti -u postgres fe_postgres psql -U folksonomy folksonomy

# Docker images take up space on the disk (hundreds of MBs). If you want to remove them at the end:
# list docker images
docker image -a

# remove a docker image by its id
docker rmi ef6f102be0da
```

To finish setup:
```bash
# create local_settings.py
cp local_settings_example.py local_settings.py

# edit local_settings.py to fit to your environment

# At the end, launch database migration tool; it will initialize the db and/or update the database if there are migrations to apply
# You can run it on a regular basis to apply new migrations
python ./db-migration.py
```

## Run locally

```
uvicorn folksonomy.api:app --reload
```
or use `--host` if you want to make it available on your local network:
```
uvicorn folksonomy.api:app --reload --host <you-ip-address>
```

## Run with a local instance of Product Opener

To deal with CORS and/or `401 Unauthorized` issues when running in a dev environment you have to deal with two things:

* both Folksonomy Engine server and Product Opener server have to run on the same domain (openfoodfacts.localhost by default for Product Opener)
* to allow authentication with the Product Opener cookie, you must tell Folksonomy Engine to use the local Product Opener instance as the authent server

To do so you can:
* edit the `local_settings.py` (copying from `local_settings_example.py`) and uncomment proposed AUTH_PREFIX and FOLKSONOMY_PREFIX entries
* use a the same host name as Product Opener when launching Folksonomy Engine server

This then should work:
```
uvicorn folksonomy.api:app --host 127.0.0.1 --reload --port 8888
```

You can then access the API at http://api.folksonomy.openfoodfacts.localhost:8888/docs
