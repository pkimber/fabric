Fabric
******

.. highlight:: bash

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
