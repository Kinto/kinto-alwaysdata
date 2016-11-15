# -*- coding: utf-8 -*-
import argparse
import base64
import logging
import os
import sys

from pyramid.paster import bootstrap


from redis import StrictRedis
from .constants import DEPLOY_QUEUE, ID_ALWAYSDATA_KEY
from .deploy import deploy_kinto_to_alwaysdata
from .status_handler import RedisStatusHandler
from .utils import hmac_digest


FILE_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(levelname)-5.5s  %(message)s"


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Kinto Deployment Worker")
    parser.add_argument('--ini',
                        help='Application configuration file',
                        dest='ini_file')

    parsed_args = vars(parser.parse_args(args))
    logging.basicConfig(level=DEFAULT_LOG_LEVEL, format=DEFAULT_LOG_FORMAT)

    config_file = parsed_args['ini_file']
    env = bootstrap(config_file)
    registry = env['registry']

    r = StrictRedis(**registry.redis)

    while True:
        queue, b64_credentials = r.blpop(DEPLOY_QUEUE, 0)
        user_id = hmac_digest(registry.hmac_secret, b64_credentials)
        credentials = base64.b64decode(b64_credentials).split(':', 1)

        id_alwaysdata = r.get(ID_ALWAYSDATA_KEY.format(user_id))

        settings = {
            'id_alwaysdata': id_alwaysdata,
            'credentials': tuple(credentials),
            'postgresql_host': "postgresql-%s.alwaysdata.net" % id_alwaysdata,
            'ssh_host': "ssh-%s.alwaysdata.net" % id_alwaysdata,
            'ftp_host': "ftp-%s.alwaysdata.net" % id_alwaysdata,
            'prefixed_username': "%s_kinto" % id_alwaysdata
        }

        status_handler = RedisStatusHandler(r, user_id)

        deploy_kinto_to_alwaysdata(status_handler, file_root=FILE_ROOT, **settings)
