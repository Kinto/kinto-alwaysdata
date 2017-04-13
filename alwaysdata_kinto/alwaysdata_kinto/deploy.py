# -*- coding: utf-8 -*-
import ftplib
import hashlib
import logging
import os
import requests

from paramiko.client import SSHClient, AutoAddPolicy
from six import StringIO

from .constants import API_BASE_URL, STATUS
from .exceptions import KintoDeployException, DatabaseAlreadyExists, SSHUserAlreadyExists

logger = logging.getLogger(__name__)


def deploy_kinto_to_alwaysdata(status_handler, id_alwaysdata, credentials, prefixed_username,
                               postgresql_host, ssh_host, ftp_host, file_root):
    # Postgresql Database
    try:
        logger.info("Create Postgresql Database")
        create_postgresql_database(id_alwaysdata, credentials, prefixed_username)
    except DatabaseAlreadyExists as e:
        logger.warn("Database exists: %s" % e)
        status_handler.database = STATUS.EXISTS
    except KintoDeployException as e:
        logger.error("Error while creating the database: %s" % e)
        status_handler.database = STATUS.ERROR
        raise
    else:
        logger.info("Database created.")
        status_handler.database = STATUS.CREATED

    # SSH User
    try:
        logger.info("Create SSH User")
        create_ssh_user(id_alwaysdata, credentials, prefixed_username)
    except SSHUserAlreadyExists as e:
        logger.warn("SSH user exists: %s" % e)
        status_handler.ssh_user = STATUS.EXISTS
    except KintoDeployException as e:
        logger.error("Error while creating the ssh user: %s" % e)
        status_handler.ssh_user = STATUS.ERROR
        raise
    else:
        logger.info("SSH user created.")
        status_handler.ssh_user = STATUS.CREATED

    # Configuration upload over FTP
    try:
        logger.info("Uploading the configuration")
        upload_configuration_files_over_ftp(id_alwaysdata, credentials, ftp_host, postgresql_host,
                                            prefixed_username, file_root)
    except KintoDeployException as e:
        logger.error("Error while uploading the configuration: %s" % e)
        status_handler.configuration = STATUS.ERROR
        return
    else:
        logger.info("Configuration uploaded")
        status_handler.configuration = STATUS.CREATED

    try:
        logger.info("Installing Kinto")
        install_kinto_remotely(id_alwaysdata, credentials, ssh_host, prefixed_username,
                               status_handler)
    except Exception as e:
        logger.error("Error while installing Kinto: %s" % e)
        status_handler.ssh_commands = STATUS.ERROR
        raise
    else:
        logger.info("Kinto installed: https://%s.alwaysdata.net/v1/" % id_alwaysdata)
        status_handler.ssh_commands = STATUS.CREATED

    # Configure site
    try:
        logger.info("Create User Site")
        configure_site(id_alwaysdata, credentials, prefixed_username)
    except KintoDeployException as e:
        logger.error("Error while configuring the user site: %s" % e)
        status_handler.user_site = STATUS.ERROR
        raise
    else:
        logger.info("User site created.")
        status_handler.user_site = STATUS.CREATED



def create_postgresql_database(id_alwaysdata, credentials, prefixed_username):
    response = requests.post(API_BASE_URL.format("/database/"), json={
        "name": prefixed_username,
        "type": "POSTGRESQL",
        "permissions": {id_alwaysdata: "FULL"}
    }, auth=credentials)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        # The database may already exist.
        if error.response.status_code != 400:
            raise KintoDeployException(error)
        raise DatabaseAlreadyExists(error)


def create_ssh_user(id_alwaysdata, credentials, prefixed_username):
    response = requests.post(API_BASE_URL.format("/ssh/"), json={
        "name": prefixed_username,
        "password": credentials[1],
    }, auth=credentials)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        # The database may already exist.
        if error.response.status_code != 400:
            raise KintoDeployException(error)
        raise SSHUserAlreadyExists(error)


def configure_site(id_alwaysdata, credentials, prefixed_username):
    response = requests.get(API_BASE_URL.format("/site/"), auth=credentials)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        # The database may already exist.
        raise KintoDeployException(error)
    current_site = None
    for site in response.json():
        print(site)
        for address in site['addresses']:
            if address == '{}.alwaysdata.net/'.format(id_alwaysdata):
                current_site = site
                break
        if current_site:
            break
    if current_site:
        print("Delete previous site.")
        requests.delete(API_BASE_URL.format("/site/{}".format(current_site['id'])),
                        auth=credentials)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            # The database may already exist.
            print(response.json())
            raise KintoDeployException(error)

    # Only one address for this site, let's change it to setup kinto on it.
    response = requests.post(API_BASE_URL.format("/site/"),
                             json={"name": "kinto", "type": "wsgi",
                                   "path": "/kinto/kinto.wsgi", "ssl_force": True,
                                   "addresses": ['{}.alwaysdata.net/'.format(id_alwaysdata)],
                                   "working_directory": "/kinto/",
                                   "virtualenv_directory": "/kinto/venv/",
                                   "static_paths": "/attachments/=/kinto/attachments/"},
                             auth=credentials)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(response.json())
        raise KintoDeployException(error)


def upload_configuration_files_over_ftp(id_alwaysdata, credentials, ftp_host, postgresql_host,
                                        prefixed_username, file_root):
    response = requests.put(API_BASE_URL.format("/environment/python/"),
                            json={"python_version": "3.6.0"},
                            auth=credentials)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print(response.json())
        raise KintoDeployException(error)

    ftp = ftplib.FTP(ftp_host, id_alwaysdata, credentials[1])

    try:
        ftp.mkd("kinto")
    except ftplib.error_perm:
        pass
    try:
        ftp.mkd("kinto/attachments/")
    except ftplib.error_perm:
        pass
    with open(os.path.join(file_root, "kinto.ini"), "rb") as f:
        ini_content = f.read().format(
            bucket_id='{bucket_id}',
            collection_id='{collection_id}',
            id_alwaysdata=id_alwaysdata,
            password=credentials[1],
            postgresql_host=postgresql_host,
            prefixed_username=prefixed_username,
            hmac_secret=hashlib.sha256(':'.join(credentials)).hexdigest())
        ftp.storbinary("STOR kinto/kinto.ini", StringIO(ini_content))

    with open(os.path.join(file_root, "kinto.wsgi"), "rb") as f:
        ftp.storbinary("STOR kinto/kinto.wsgi", f)
        ftp.sendcmd('SITE CHMOD 755 kinto/kinto.wsgi')

    ftp.close()


def install_kinto_remotely(id_alwaysdata, credentials, ssh_host, prefixed_username,
                           status_handler):
    logs = StringIO()
    # SSH Login
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ssh_host, username=prefixed_username, password=credentials[1], look_for_keys=False)

    # Create virtualenv
    stdin, stdout, stderr = ssh.exec_command(
        'virtualenv kinto/venv/'
    )
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Install Kinto in the virtualenv
    stdin, stdout, stderr = ssh.exec_command(
        'kinto/venv/bin/pip install kinto[postgresql] kinto-attachment'
    )
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Run kinto migration to setup the database.
    stdin, stdout, stderr = ssh.exec_command('kinto/venv/bin/kinto migrate --ini kinto/kinto.ini')
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs
    ssh.close()
