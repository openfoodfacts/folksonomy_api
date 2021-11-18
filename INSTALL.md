# HOWTO install/test Folksonomy API

## Requirements

- Postgresql 13 (lower version may be OK, but untested)
- Python 3.8 (lower version may be ok too, but untested)
- Python modules in "requirements.txt"

## Setup

```
# clone repo
git clone https://github.com/cquest/folksonomy_api.git
cd folksonomy_api

# required packages to setup a virtualenv (optional, but recommended)
apt install python3-virtualenv virtualenv virtualenvwrapper

# create and switch to virtualenv
mkvirtualenv folksonomy -p /usr/bin/python3
workon folksonomy

# install 
pip install -r requirements.txt

# create dbuser if needed
sudo -u postgres createuser $USER

# create Postgresql database
sudo -u postgres createdb folksonomy -O $USER
psql folksonomy < db/db_setup.sql

```

## Run locally

```
uvicorn folksonomy.api:app --reload
```
or use `--host` if you want to make it available on your local network, eg.:
```
uvicorn folksonomy.api:app --reload --host 192.168.0.100
```

## Run with a local instance of Product Opener

```
uvicorn folksonomy.api:app --reload --host api.folksonomy.openfoodfacts.localhost
```
You also have to modify `auth_server` variable in `/folksonomy/api.py`.
