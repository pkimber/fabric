Fabric
******

.. highlight:: bash

::

  apt-get install python-dev
  apt-get install duplicity python-paramiko

The documentation for this project can be found at:
https://github.com/pkimber/docs

To create the python **2** virtual environment for this project::

  # deactivate any current virtual environments
  deactivate

  virtualenv venv-fabric
  source venv-fabric/bin/activate
  pip install -r requirements.txt

To activate the environment::

  source venv-fabric/bin/activate

To run the unit tests::

  source venv-fabric/bin/activate
  py.test -x

Important
=========

.. important:: ``devpi`` (python ``requests``) on python 2 isn't happy with the
               new SSL certificate on our devpi server.  ``devpi`` with python
               3 is happy - so use ``devpi`` with python 3.
