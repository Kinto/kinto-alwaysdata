# auto-kinto-alwaysdata

Deploy a Kinto on AlwaysData automatically.

**/!\ this is highly alpha, and should only be run on an empty
[AlwaysData](https://alwaysdata.com) account /!\**

1. create an account on [AlwaysData](https://alwaysdata.com)
2. connect to http://kinto.github.io/kinto-alwaysdata/
3. enter your email/password
4. click the big "Deploy my Kinto!" button

It will add a task for the worker to automatically install and launch a kinto
instance on your account, using the
[deploy-kinto.py](https://github.com/Kinto/kinto-alwaysdata/blob/master/deploy-kinto.py)
script.
