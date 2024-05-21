# -*- coding: utf-8 -*-
import tempfile

import pytest

from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.util.files import resolveDir

expected_db_version = 1
expected_tables = {
  "DB_INFO",
  "DELTA_NEUTRAL_CONTRACT",
  "CONTRACT",
  "COMBO_LEG",
  "CONTRACT_DETAIL_TAG",
  "CONTRACT_DETAILS",
  "MOVEMENT",
  "ORDER_T"
}


@pytest.fixture
def setup_db() -> TradingDB:
  ndb = new_db()
  v = ndb.ensure_version(expected_db_version)
  assert v and v.version == expected_db_version
  return ndb


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


def test_db_init(setup_db: TradingDB) -> None:
  with setup_db as conn:
    with conn.cursor() as crs:
      tables = crs.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
      assert sorted(t[0].upper() for t in tables) == sorted(expected_tables)
