# kinto-alwaysdata

Deploy a Kinto on AlwaysData automatically.

## Get started shortly

**/!\ this is highly alpha, and should only be run on an empty
[AlwaysData](https://alwaysdata.com) account /!\**

1. Create an account on [AlwaysData](https://alwaysdata.com)
2. Connect to http://kinto.github.io/kinto-alwaysdata/
3. Enter your email/password
4. Click the big "Deploy my Kinto!" button

It will add a task for the worker to automatically install and launch a kinto
instance on your account, using the
[kinto-alwaysdata](https://github.com/Kinto/kinto-alwaysdata/blob/master/alwaysdata_kinto/alwaysdata_kinto/deploy.py)
script.


## Installation locally

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
