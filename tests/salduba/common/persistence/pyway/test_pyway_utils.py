import logging
import tempfile
from pathlib import Path

from salduba.common.configuration import DbConfig
from salduba.common.persistence.pyway.migrating import init_db
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

# import pytest

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


def test_migrate() -> None:
  temp = tempfile.NamedTemporaryFile()
  file_name = Path(temp.name)
  temp.close()

  dbConfig = DbConfig(
    storage_name=str(file_name.absolute()),
    echo=True
  )

  init_db(dbConfig)
