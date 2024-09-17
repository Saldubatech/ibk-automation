Cervino Trade Automation User Guide
***********************************

Installation
==============

Mac/Unix
---------

1. Ensure there is a `Version of Python <https://www.python.org/downloads/>`_ installed in your system. The application is developed against Python 3.11, 3.12 has not been tested and is known to have some incompatibilities with some libraries that have not been upgraded yet. It is likely that this problem will disappear with time.
2. *Optional* create and activate a virtual environment to isolate the packages for this application:

.. code-block:: shell

  % python -m venv <path-to-virtual-env-location>
  % source <path-to-virtual-env-location>/bin/activate
  % pip install --upgrade pip

3. Install the application:

.. code-block:: shell

  % pip install salduba_corvino

If looking for a version that is only in ``test-pypi``

.. code-block::shell

  % pip install --extra-index-url https://test.pypi.org/simple/ salduba_corvino==<version_identifier>

Windows
--------

- Install Python
- env
- Add to Path in powershell: `$Env:PATH = "<env-path>;$Env:PATH"`
- Create `c:\tmp` directory to enable logs.
- corvino_cli --help
- Install Tws & Login. Allow all requests presented.

Usage
=======

The application is a command line application to be executed from a Shell (e.g. Windows Powershell or Unix/Mac Terminal with bash or zsh)

Once installed (with the Venv active if configured), the entry point command is `corvino_cli` which prints the following help information:

.. code-block:: shell

  % corvino_cli

  Usage: corvino_cli [OPTIONS] COMMAND [ARGS]...

  Options:
    -c, --config TEXT  Path to the configuration file to use
    --help             Show this message and exit.

  Commands:
    lookup-contracts
    place-orders
    verify-contracts
  %

The only option is to provide an alternative path to the :doc:`configuration_file` for the application.

If not specified, the application looks for the file in the following locations in order:

1. In a `.cervino` folder under the user `HOME` directory:

  - In Windows: ``C:\Users\<username>\.cervino/cervino_config.yml``
  - In mac and ``*nix`` systems: ``/Users/<username>/.cervino/cervino_config.yml``

2. The user's *configuration* directory:

  - In Windows: ``C:\Users\<username>\??`` **NOTE: TO-DO check Windows location for this**
  - In mac and ``*nix`` systems: `/Users/<username>/.config/cervino_config.yml`

3. The user's *Documents* directory:

  - In Windows: ``C:\Users\<username>\Documents\cervino_config.yml``
  - In mac and ``*nix`` systems: ``/Users/<username>/Documents/cervino_config.yml```

4. The user's *Desktop* directory:

  - In Windows: ``C:\Users\<username>\Desktop\cervino_config.yml``
  - In mac and ``*nix`` systems: ``/Users/<username>/Desktop/cervino_config.yml```

If it does not find it anywhere, it will create a default configuration file in the first directory that it finds in the same order.

The Commands available are:

1. ``verify-contracts`` to check if contract information is available in the local DB to perform the trades. This command does not require the `TWS` application to be running. Missing Contracts will
    be written to the mising output file specified in the option or to `missing-contracts.csv` in the current folder.
2. ``lookup-contracts`` To retrieve from ``TWS`` any information needed for the movements in the input file and refresh information that is older than the expiration period (currently 3 months)
3. ``place-orders`` load all the movements specified in the input file to ``TWS`` the application must be running in the local machine listening on port `7497`

To execute a movements file, the format is:

``corvino_cli [OPTIONS] <command> <FILE>``

Where `<FILE>` is the path to the ``csv`` of ``xlsx`` file.

If it is a ``xlsx`` file, it should have a sheet with the name specified in the configuration file (by default ``Movements``)

The file **must** have the columns:

- **Ticker**: A String with the Symbol for the security, a two letter code for the country in which it should be traded and the type of Security to trade, which currently can only be `Equity`.
- **Trade**: The desired trade in number of units to trade (integer). Positive if it is to buy and negative if it is to sell.

The rest of columns in the file will be ignored

These commands will produce a results file with the name provided in the configuration file in **Excel**:sup:`(TM)` ``xlsx`` format with the following sheets:

- ``inputs``: The information from the input file, as parsed and processed by the application
- ``known``: The securities that were already known to the application before the command execution
- ``updated``: The securities that were updated during the execution of the command, if applicable (for the ``lookup-contracts`` command)
- ``missing``: The securities from the input file that are not known to the system. For the ``verify-contracts`` this is the simple result of checking against
  internal information, for ``lookup-contracts`` and ``place-orders`` this is the result after attempting to lookup securities in the ``TWS`` api.
- ``movement``: The orders placed by the command if any.
- ``errors``: A list of the errors that the system has received from the ``TWS`` api, if any.

The names of these sheets and the name of the output file can be overridden in the configuration file.

Commands that need to communicate with the `TWS <https://www.ibkrguides.com/traderworkstation/api.htm?Highlight=api%20connection>`` service need the service
available in the host (default ``localhost``) and the port (default `7497`) specified in the configuration file.

Check the information in `TWS documents <https://www.ibkrguides.com/traderworkstation/api.htm?Highlight=api%20connection>` for how to configure alternative ports
or allow connection from other computers in case these need to change.


Verify Contracts Command
------------------------------

The ``verify-contracts`` command:

.. code-block:: shell

  % corvino_cli verify-contracts --help
  Usage: corvino_cli verify-contracts [OPTIONS] INPUT_MOVEMENTS_FILE

  Options:
    --help Show this message and exit.

Will check the securities specified in the input file and report the known and missing ones in the output file as defined in the previous file.

Lookup Contracts Command
---------------------------

The ``lookup-contracts`` command:

.. code-block:: shell
  % poetry run corvino_cli lookup-contracts --help
  Usage: corvino_cli lookup-contracts [OPTIONS] INPUT_MOVEMENTS_FILE

  Options:
    --help  Show this message and exit.

Checks the input file against its internal information and looks up any securities that are not known against the TWS system. It will update its internal information
with any new securities in the input file or refresh the information for securities with information older than 3 months. It will provide the results in the output
file.

Place Orders command
---------------------

.. code-block:: shell
  % corvino_cli place-orders --help
  Usage: corvino_cli place-orders [OPTIONS] INPUT_MOVEMENTS_FILE

  Options:
    --batch TEXT      The name of the batch to use for these orders, default:
                      Date with seconds (Year-Month-Day:Hour:min:secs)

    --execute-trades  USE WITH CAUTION!!!!

                      - If the option is provided, the script will execute the
                      trades directly, - If not provided, the trades will be
                      uploaded but not executed. The user is then expected to
                      execute them if appropriate using the TWS UI itself

    --help            Show this message and exit.

Takes the following options:

- ``--batch`` to specify an alternative name to identify the batch of orders in the input file. The default name is: ``<batch_prefix>_YYYYMMDDHHmmss`` with the ``batch_prefix``
  specified in the configuration file, with a default of ``order_batch``
- ``--execute-trades``: If this flag is provided, the system will attempt to execute the trades directly instead of only uploading them for later manual review and submission.

This command will take the trades specified in the input file and upload them to the TWS service with the contract information in its internal database. If any trade refers
to a contract that is not known to the system, no trades will be executed and the information on what contract information will be provided in the output file. If this happens
the user can execute the ``lookup-contracts`` command to try to recover the information from TWS, or they may need to correct the information in the input file.
