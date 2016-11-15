# -*- coding: utf-8 -*-
import ftplib
import hashlib
import logging
import os
import requests

from paramiko import ssh_exception
from paramiko.client import SSHClient, AutoAddPolicy
from six import StringIO
from time import sleep

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


def upload_configuration_files_over_ftp(id_alwaysdata, credentials, ftp_host, postgresql_host,
                                        prefixed_username, file_root):
    ftp = ftplib.FTP(ftp_host, id_alwaysdata, credentials[1])

    try:
        ftp.mkd(".local")
    except ftplib.error_perm:
        pass
    try:
        ftp.mkd("kinto")
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

    with open(os.path.join(file_root, "kinto.fcgi"), "rb") as f:
        ftp.storbinary("STOR www/kinto.fcgi", f)
        ftp.sendcmd('SITE CHMOD 755 www/kinto.fcgi')
        try:
            ftp.delete('www/index.html')
        except ftplib.error_perm:
            pass

    with open(os.path.join(file_root, "htaccess"), "rb") as f:
        ftp.storbinary("STOR www/.htaccess", f)
    ftp.close()


def install_kinto_remotely(id_alwaysdata, credentials, ssh_host, prefixed_username,
                           status_handler):
    logs = StringIO()
    # SSH Login
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(ssh_host, username=prefixed_username, password=credentials[1], look_for_keys=False)

    # Install pip
    retry = 30
    error = None
    while retry > 0:
        try:
            stdin, stdout, stderr = ssh.exec_command(
                'PYTHONPATH=~/.local/ easy_install-2.6 --install-dir=~/.local -U pip'
            )
            retry = 0
        except ssh_exception.AuthenticationException as e:
            error = e
            sleep(5)
            retry -= 1

    if retry == 0 and error is not None:
        logs.write(error)

    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Install virtualenv
    stdin, stdout, stderr = ssh.exec_command(
        'PYTHONPATH=~/.local/ ~/.local/pip install --user --no-binary --upgrade '
        'setuptools virtualenv virtualenvwrapper'
    )
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Create virtualenv
    stdin, stdout, stderr = ssh.exec_command(
        '~/.local/bin/virtualenv kinto/venv/ --python=python2.7'
    )
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Install Kinto in the virtualenv
    stdin, stdout, stderr = ssh.exec_command(
        'kinto/venv/bin/pip install kinto[postgresql] kinto-attachment flup'
    )
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs

    # Run kinto migration to setup the database.
    stdin, stdout, stderr = ssh.exec_command('kinto/venv/bin/kinto --ini kinto/kinto.ini migrate')
    logs.write(stdout.read())
    logs.write(stderr.read())
    status_handler.ssh_logs = logs
    ssh.close()
