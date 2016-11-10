#!/usr/bin/eval python2.7
import os
here = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Activate the virtualenv
activate_this = os.path.join(here, 'kinto', 'venv', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

from flup.server.fcgi_fork import WSGIServer

try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import logging.config

from kinto import main

ini_path = os.path.join(here, 'kinto', 'kinto.ini')

# Set up logging
logging.config.fileConfig(ini_path)

# Parse config and create WSGI app
config = configparser.ConfigParser()
config.read(ini_path)

class ScriptNameStripper(object):
   def __init__(self, app):
       self.app = app

   def __call__(self, environ, start_response):
       environ['SCRIPT_NAME'] = ''
       return self.app(environ, start_response)

application = main(config.items('DEFAULT'), **dict(config.items('app:main')))

server = WSGIServer(ScriptNameStripper(application))
server.run()
