# Folksonomy API Installation Guide

## Requirements

- PostgreSQL 13 or newer
- Python 3.9 or newer
- Python modules in "requirements.txt"

## Setup on Debian 12 (Recommended Method)

```bash
# Start with a fresh Debian 12 install, logged as root
apt install git sudo postgresql python3-venv -y

# Create a user for the application (optional but recommended)
adduser folksonomy
usermod -aG sudo folksonomy
su folksonomy
cd ~

# Clone repo
git clone https://github.com/openfoodfacts/folksonomy_api.git
cd folksonomy_api

# Create and activate Python virtual environment
python3 -m venv folksonomy
. ./folksonomy/bin/activate

# Install required packages
pip install -r requirements.txt

# Set up PostgreSQL database
sudo -i -u postgres createuser $USER
sudo -i -u postgres createdb folksonomy -O $USER

# Initialize the database using yoyo-migrations
yoyo apply --database postgresql:///folksonomy

# Create local settings file
cp local_settings_example.py local_settings.py
# Edit local_settings.py to fit your environment if needed

# Run the application
uvicorn folksonomy.api:app --reload --host <your-ip-address>
```

## Alternative Setup Methods

### Using virtualenvwrapper

```bash
# Clone repo
git clone https://github.com/openfoodfacts/folksonomy_api.git
cd folksonomy_api

# Required packages to setup a virtualenv (optional, but recommended)
apt install python3-virtualenv virtualenv virtualenvwrapper

# Create and switch to virtualenv
# If mkvirtualenv command is not found, search for virtualenvwrapper.sh
# create and switch to virtualenv
# if mkvirtualenv command is not found, search for virtualenvwrapper.sh
# (/usr/share/virtualenvwrapper/virtualenvwrapper.sh, or /usr/bin/virtualenvwrapper.sh, for example)

# Add the path in your bash profile
mkvirtualenv folksonomy -p /usr/bin/python3
workon folksonomy

# install
pip install -r requirements.txt
```
If you install PostgreSQL yourself, here is how to set it up:

```bash
# Create dbuser if needed
sudo -u postgres createuser $USER

# Create Postgresql database if needed
sudo -u postgres createdb folksonomy -O $USER
psql folksonomy < db/db_setup.sql
```
Otherwise, you can use the `./start_postgres.sh` which launch a ready to use Postgres Docker container. You don't have to install Postgres but you need to have Docker installed. Here are some tips to use it:
```bash
# Launch Postgres Docker container
./start_postgres.sh # Have a look at the log messages

# You can also launch it in the background
./start_postgres.sh & # but log messages are not displayed anymore

# If you have launched the container in the background, stop the container like this:
docker stop fe_postgres

# If you want to use psql inside the Docker container:
docker exec -ti -u postgres fe_postgres psql -U folksonomy folksonomy

# Docker images take up space on the disk (hundreds of MBs). If you want to remove them at the end:
# List docker images
docker image -a

# Remove a docker image by its id
docker rmi ef6f102be0da
```

To finish setup:
```bash
yoyo apply --database postgresql:///folksonomy
```

Alternatively, you can use the original migration script:
```bash
# At the end, launch database migration tool; it will initialize the db and/or update the database if there are migrations to apply
# You can run it on a regular basis to apply new migrations
python ./db-migration.py
```

## Run locally

```bash
uvicorn folksonomy.api:app --reload
```

or use `--host` if you want to make it available on your local network:
```
uvicorn folksonomy.api:app --reload --host <you-ip-address>
```

## Authentication and Adding Data to the Database

### Prerequisites

- A local PostgreSQL database must be running.
- Your local server must be running; try http://127.0.0.1:8000 in your browser.
- You must have an account at https://world.openfoodfacts.org and your login credentials.

### Steps to Authenticate

- Open https://127.0.0.1:8000/docs.
- Click on the "Authorize" button in the API documentation interface.
- Log in with your credentials.
- Once authenticated, you can start making API requests to add data from the interface.

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
