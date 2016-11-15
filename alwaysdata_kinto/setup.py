import codecs
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    """Open a related file and return its content."""
    with codecs.open(os.path.join(here, filename), encoding='utf-8') as f:
        content = f.read()
    return content

README = read_file('README.rst')

ENTRY_POINTS = {
    'paste.app_factory': [
        'main = alwaysdata_kinto:main',
    ],
    'console_scripts': [
        'alwaysdata-kinto-worker = alwaysdata_kinto.worker:main'
    ],
}


setup(name='alwaysdata_kinto',
      version=0.1,
      description='Deploy Kinto on your Alwaysdata.',
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords="web services",
      author='',
      author_email='',
      url='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=['cornice', 'waitress', 'paramiko', 'redis', 'requests', 'six'],
      entry_points=ENTRY_POINTS,
      paster_plugins=['pyramid'])
