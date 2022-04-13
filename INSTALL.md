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

To deal with CORS and/or `401 Unauthorized` issues when running in a dev environment you have to deal with two things:
* both Folksonomy Engine server and Product Opener server have to run on the same domain (openfoodfacts.localhost by default for Product Opener)
* to allow authentication with the Product Opener cookie, you must tell Folksonomy Engine to use the local Product Opener instance as the authent server

To do so you can:
* add an environment variable, `AUTH_URL` to specify the auth server
* use a the same host name as Product Opener when launching Folksonomy Engine server

This should work:
```
AUTH_URL="http://fr.openfoodfacts.localhost" uvicorn folksonomy.api:app --host 'api.fr.openfoodfacts.localhost' --reload
```
