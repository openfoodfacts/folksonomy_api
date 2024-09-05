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

# create dbuser if needed
sudo -u postgres createuser $USER

# create Postgresql database if needed
sudo -u postgres createdb folksonomy -O $USER
psql folksonomy < db/db_setup.sql

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
