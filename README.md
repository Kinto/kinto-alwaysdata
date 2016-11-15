# kinto-alwaysdata

Deploy a Kinto on AlwaysData automatically.

## Installation

1. Clone the repository
2. Install the package: ```pip install -e alwaysdata_kinto```

## Using the CLI tool

Run the following command to deploy from your computer:

```kinto-alwaysdata --auth email@tld.com```

It will ask your password and everything will flow from there.

## Using the Web Interface

Just reach to https://kinto.github.io/kinto-alwaysdata/

If you wish to serve it locally:

1. Run a redis-server: ```sudo apt-get install redis-server```
2. Run the web server: ```make serve```
3. Run the worker: ```make worker```
4. Run the web interface: ```make web```
