# Folksonomy API Installation Guide
  This guide will walk you through installing and setting up the Folksonomy API on a fresh Debian 12 system.

 ## Prerequisites
 A fresh Debian 12 installation

 Root access or a user with sudo privileges

 Basic knowledge of the command line

## Step 1: Install required packages

```apt install git sudo postgresql python3-venv -y```


## Step 2: Create a New User for Folksonomy API
For security reasons, it's recommended to run the API under a separate user.

### Create a new user for the Folksonomy API
   ```adduser folksonomy```

### Add the new user to the sudo group to allow elevated permissions when needed
```usermod -aG sudo folksonomy```

### Switch to the newly created user:
```su folksonomy```

# Step 3: Clone the Repository
## Navigate to your home directory and clone the Folksonomy API repository.

```
cd ~
git clone https://github.com/openfoodfacts/folksonomy_api.git
cd folksonomy_api
```

# Step 4: Set Up a Python Virtual Environment
### To isolate the API's dependencies, create and activate a Python virtual environment:

```bash
python3 -m venv folksonomy
. ./folksonomy/bin/activate
```

# Step 5: Install Python Dependencies
### Once the virtual environment is activated, install the required Python dependencies from requirements.txt.

```pip install -r requirements.txt```

# Step 6: Set Up PostgreSQL Database
### Create a PostgreSQL user and database for the Folksonomy API.

## Create a new PostgreSQL user for the Folksonomy API
```sudo -i -u postgres createuser $USER```

## Create a new PostgreSQL database for the Folksonomy API, owned by the user
```sudo -i -u postgres createdb folksonomy -O $USER```

## Apply the migrations to set up the database schema:
```yoyo apply --database postgresql:///folksonomy```

```
#Otherwise, you can use the `./start_postgres.sh` which launch a ready to use Postgres Docker container. You don't have to install Postgres but you need to have Docker installed. Here are some tips to use it:
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

# Step 7: Configure the API

```bash
# create local_settings.py
cp local_settings_example.py local_settings.py

# edit local_settings.py to fit to your environment

# At the end, launch database migration tool; it will initialize the db and/or update the database if there are migrations to apply
# You can run it on a regular basis to apply new migrations
python ./db-migration.py
```

# Step 8: Run the API
### Start the API using Uvicorn. Replace <my_ip_address_or_domain_name> with the IP address or domain name of your server.

```uvicorn folksonomy.api:app --reload --host <my_ip_address_or_domain_name>```

### This will start the Folksonomy API and reload automatically when you make changes to the code.

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

## Conclusion
You should now have the Folksonomy API running on your Debian 12 system. You can access it at http://<my_ip_address_or_domain_name>:8000 (or any other port you configure). Make sure to refer to the official documentation for more advanced configuration options.

For further help, feel free to open an issue or contribute to the project!