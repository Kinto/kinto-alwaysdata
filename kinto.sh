#!/bin/bash

# site:
#     type: wsgi
#     path: '{INSTALL_PATH_RELATIVE}/app.wsgi'
#     environment: KINTO_INI=config/alwaysdata.ini
#     python_version: '3.7'
#     virtualenv_directory: '{INSTALL_PATH_RELATIVE}/env'
# database:
#     type: postgresql

set -e

# Python environment
python -m venv env
source env/bin/activate
pip install kinto[postgresql]

# WSGI
wget https://raw.githubusercontent.com/Kinto/kinto/master/app.wsgi

# Application configuration
CONFIGURATION_FILE="config/alwaysdata.ini"
POSTGRESQL_CONNECTION="postgres://$DATABASE_USERNAME:$DATABASE_PASSWORD@$DATABASE_HOST/$DATABASE_NAME"
kinto init --ini $CONFIGURATION_FILE --backend postgresql --cache-backend postgresql
sed -i "s|^kinto.storage_url = .*|kinto.storage_url = $POSTGRESQL_CONNECTION|" $CONFIGURATION_FILE
sed -i "s|^kinto.cache_url = .*|kinto.cache_url = $POSTGRESQL_CONNECTION|" $CONFIGURATION_FILE
sed -i "s|^kinto.permission_url = .*|kinto.permission_url = $POSTGRESQL_CONNECTION|" $CONFIGURATION_FILE
kinto migrate --ini $CONFIGURATION_FILE
