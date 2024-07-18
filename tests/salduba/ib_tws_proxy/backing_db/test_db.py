# -*- coding: utf-8 -*-
import tempfile
from typing import Optional

import pytest

from salduba.common.configuration import DbConfig
from salduba.ib_tws_proxy.backing_db.db import TradingDB

config = DbConfig(
  storage_name="tests/resources_test_db.db",
  min_required_version=1
)

local_db: Optional[TradingDB] = None


@pytest.fixture
def setup_db() -> TradingDB:
  return new_db()


def new_db() -> TradingDB:
  temp = tempfile.NamedTemporaryFile()
  temp.close()
  local_config = DbConfig(
    storage_name=temp.name,
    min_required_version=1
  )
  return TradingDB(local_config)


def test_db_connection(setup_db: TradingDB) -> None:
  with setup_db as db:
    assert db.conn
    assert db.connection_depth == 1
  assert setup_db.connection_depth == 0
  assert not setup_db.conn


def test_0_version() -> None:
  with new_db() as local_db:
    assert not local_db.version()
    validation_1 = local_db.validate(1)
    ensure_v0 = local_db.ensure_version(0, True)
    assert not validation_1
    assert not ensure_v0, f"Finding : {ensure_v0}"


def test_ensure_version(setup_db: TradingDB) -> None:
  with setup_db as db:
    v = db.ensure_version(1)
    assert v and v.version == 1, f"Version is {v}"
