# -*- coding: utf-8 -*-
import tempfile

import pytest

from salduba.common.configuration import DbConfig
from salduba.ib_tws_proxy.backing_db.db import TradingDB

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
  local_config = DbConfig(
    storage_name=temp.name,
    min_required_version=1
  )
  return TradingDB(local_config)


def test_db_init(setup_db: TradingDB) -> None:
  with setup_db as conn:
    with conn.cursor() as crs:
      tables = crs.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
      assert sorted(t[0].upper() for t in tables) == sorted(expected_tables)
