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
sudo su - postgres -c "createuser $USER"

# create Postgresql database
sudo su - postgres -c "createdb folksonomy -O $USER"
sudo su - postgres -c 'psql -c "grant all privileges on database folksonomy to $USER;"'
sudo su postgres -c "psql folksonomy < db/db_setup.sql"

```

## Run locally

```
uvicorn folksonomy.api:app --reload
```
or use `--host` if you want to make it available on your local network, eg.:
```
uvicorn folksonomy.api:app --reload --host 192.168.0.100
```
