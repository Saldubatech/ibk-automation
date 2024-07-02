Corvino Trade Automation User Guide
***********************************

Installation
==============


1. Ensure there is a `Version of Python <https://www.python.org/downloads/>`_ installed in your system. The application is developed against Python 3.11, 3.12 has not been tested and is known to have some incompatibilities with some libraries that have not been upgraded yet. It is likely that this problem will disappear with time.
2. *Optional* create and activate a virtual environment to isolate the packages for this application:

.. code-block:: shell

  % python -m venv <path-to-virtual-env-location>
  % source <path-to-virtual-env-location>/bin/activate
  % pip install --upgrade pip

3. Install the application:

.. code-block:: bash

  % pip install salduba_corvino

If looking for a version that is only in  ``test-pypi``

.. code-block:: bash

  % pip install --extra-index-url https://test.pypi.org/simple/ salduba_corvino==<version_identifier>

Usage
=======

The application is a command line application to be executed from a Shell (e.g. Windows Powershell or Unix/Mac Terminal with bash or zsh)

Once installed (with the Venv active if configured), the entry point command is:

.. code-block:: bash

  % corvino_cli

  Usage: corvino_cli [OPTIONS] COMMAND [ARGS]...

  Options:
    -db, --database TEXT   Path to the database to use
    --missing-output TEXT  Path to the output for missing contracts, it must be
                          a *.csv file
    --movement-sheet TEXT  If the input is a xlsx file with more than one sheet,
                          the name of the sheet with the Movements
    --help                 Show this message and exit.
  %


It prints a summary usage when invoked without arguments.

The options are:

- ``-db`` or ``--database``: The path to a file location to use as database for the system to keep information between executions of the tool. This DB is used to keep memory of Contract information, etc... to avoid querying the IBK server repeatedly if the information is already known. If not provided it defaults to a file in the user's `home` directory : `$HOME/.corvino/corvino.db`
- ``--missing-output`` the path to a file location where the application will write information about missing contract information. If not provided it will write a file in the folder where the command is executed with the name `missing-contracts.csv`
- ``--movement-sheet`` The name of the sheet for multi-sheet `xlsx` files as input. If not provided it will look for a sheet named `Movements`

The Commands available are:

1. ``verify-contracts`` to check if contract information is available in the local DB to perform the trades. This command does not require the `TWS` application to be running. Missing Contracts will be written to the mising output file specified in the option or to `missing-contracts.csv` in the current folder.
2. ``lookup-contracts`` To retrieve from `TWS` any information needed for the movements in the input file and refresh information that is older than the expiration period (currently 3 months)
3. ``place-orders`` load all the movements specified in the input file to `TWS` the application must be running in the local machine listening on port `7497`

To execute a movements file, the format is:

``corvino_cli <command> <FILE>``

Where ``<FILE>`` is the path to the csv of xlsx file.

The file needs to have the columns:

- **Ticker**: A String with the Symbol for the security, a two letter code for the country in which it should be traded and the type of Security to trade, which currently can only be `Equity`.
- **Trade**: The desired trade in number of units to trade (integer). Positive if it is to buy and negative if it is to sell.

The rest of columns in the file will be ignored
