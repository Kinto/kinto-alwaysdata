===============================
Deploy Kinto on your Alwaysdata
===============================

How to install?
===============

.. code-block:: bash

    pip install alwaysdata-kinto


How to use it?
==============


Deploy with the web interface
-----------------------------

You can either use the web interface:

.. code-block:: bash

    pserve alwaysdata_kinto.ini --reload

And then load http://localhost:8000/


Deploy with the CLI tool
------------------------

.. code-block:: bash

    deploy_to_alwaysdata --auth email@tld.com

The command will ask you your password and take you through the steps.
