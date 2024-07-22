Notes on development environment and How-to
*********************************************


General
========

1. Although only the columns described in :doc:`user_guide` will be used, the application may fail if other columns are not available in the file. This is under current testing.
2. Need testing with XLS files.
3. The Log Level can be controlled by putting a file in the `$HOME/.cervino` folder named `logging.yaml` with the regular python logging format.

Versioning
=============

In ``pyproject.toml`` as an example:

.. code-block:: toml

  version = "1.0.0a0.post2"


Following Poetry's [versioning convention](https://python-poetry.org/docs/cli/#version) and the general [Python Packaging Version Specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/#version-specifiers)

Needs to be updated by hand or using poetry each time it is published:

1. If it is for general use:
   1. Patches increment the `z` digit.
   2. Adding functionality that is backward compatible **AND** introduce little or no risk of breaking existing functionality (i.e. no major refactors or changes to underlying libraries), update the `y` digit and start with `x.Y.0`
   3. Any bigger changes in functionality or risk in implementation, change the `x` digit and start with `X.0.0`
2. If it is not for general use:
   1. Change the main digits following the rule above.
   2. Add `.aN`, or `.bN` or `.rcN` to indicate `alpha`, `beta` or `release candidate` quality
3. The *post-release* specifiers `.postN` will be used for rapid iteration of a published release if necessary, but preferably avoided.

## Publishing to PyPi or Test PyPi

It will be done using `poetry publish` documented [here](https://python-poetry.org/docs/cli#publish).

To configure it:

1. First Check the configuration with `poetry config list` and check the `repositories` entries. E.g. `repositories.testpypi.url`
2. [add a repository](https://python-poetry.org/docs/repositories/) if needed. Pypi is added by default.
3. And configure the [credentials for the repository](https://python-poetry.org/docs/repositories/#configuring-credentials) with the command `poetry config `pypi-token.<repo> <token>` with the token obtained from each repo.
4. Currently credentials are configured for `pypi` and `testpypi`

invoke the command selecting the repository if needed. By default it goes to `pypi`:

```shell
% poetry publish --repository <repository name>
```

Where `repository-name` is the name given in the repository configuration (e.g. `testpypi`)
