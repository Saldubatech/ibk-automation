# -*- coding: utf-8 -*-
import tempfile
from typing import Optional

import pytest

from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.util.files import resolveDir

config = DbConfig(
  {
    "path": "tests/resources/test_db.db",
    "schemas": "salduba/ib_tws_proxy/backing_db/schema",
    "seed_data": "salduba/ib_tws_proxy/backing_db/seed-data",
    "expected_version": "0",
    "target_version": "1",
    "version_date": "2024-02-01 00:00:00.000",
  }
)

local_db: Optional[TradingDB] = None


@pytest.fixture
def setup_db() -> TradingDB:
  return new_db()


def new_db() -> TradingDB:
  temp = tempfile.NamedTemporaryFile()
  temp.close()
  schemata = resolveDir("salduba/ib_tws_proxy/backing_db/schema")
  seed_data = resolveDir("salduba/ib_tws_proxy/backing_db/seed-data")
  if not schemata or not seed_data:
    raise Exception("Schema or Seed Data directories not found")
  local_config = DbConfig(
    {
      "path": temp.name,
      "schemas": schemata,
      "seed_data": seed_data,
      "expected_version": "0",
      "target_version": "1",
      "version_date": "2024-02-01 00:00:00.000",
    }
  )
  return TradingDB(local_config)


def test_db_connection(setup_db: TradingDB) -> None:
  with setup_db as db:
    assert db.conn
    assert db.connection_depth == 1
  assert setup_db.connection_depth == 0
  assert not setup_db.conn


def test_0_version() -> None:
  print("WHERE IS THE LOG?????????????????????????????????????????????????????????????????????????????????????")
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
