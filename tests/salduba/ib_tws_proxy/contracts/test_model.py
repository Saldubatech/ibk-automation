# -*- coding: utf-8 -*-
import datetime
import tempfile
from uuid import uuid4

import pytest

from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo
from salduba.ib_tws_proxy.contracts.model import ContractRecord
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType
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


def test_contract_record(setup_db: TradingDB) -> None:
  probe = ContractRecord(
    rid=str(uuid4()),
    at=int(datetime.datetime.now().timestamp() * 1000),
    expires_on=1111,
    conId=12345,
    symbol="SYMBOL",
    secType=SecType.STK,
    lastTradeDateOrContractMonth="March",
    strike=77.88,
    right="RIGHT",
    multiplier="MULTI",
    exchange=Exchange.SMART,
    currency=Currency.USD,
    localSymbol="L_SYMBOL",
    primaryExchange=Exchange.NYSE,
    tradingClass="TR_CLASS",
    secIdType="SEC_ID_TYPE",
    secId="SEC_ID",
    combo_legs_description="COMBO_LEGS_DESC",
    delta_neutral_contract_fk=None,
    includeExpired=True
  )
  probe_values = probe.values()
  dnc_repo = DeltaNeutralContractRepo(setup_db)
  repo = ContractRepo(setup_db, dnc_repo)

  with setup_db as db:
    with db.cursor() as crs_inserter:
      tables = crs_inserter.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
      assert set([t[0].upper() for t in tables]) == expected_tables

      crs_inserter.execute(repo.value_inserter, probe_values)
    with db.cursor() as crs_reader:
      tables = crs_reader.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
      assert set([t[0].upper() for t in tables]) == expected_tables
      records = crs_reader.execute(repo.selector + ";").fetchall()
      assert len(records) == 1, "Should have only one record: {}".format(records)
      assert records[0] == probe_values, "Values should match: \n\t{}\n\t{}".format(records[0], probe_values)
