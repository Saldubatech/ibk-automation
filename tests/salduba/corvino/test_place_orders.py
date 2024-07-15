import datetime
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import pytest

from salduba.corvino.io.parse_input import InputParser, InputRow
from salduba.corvino.persistence.movement_record import MovementRepo
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo, OrderStatusRepo, SoftDollarTierRepo
from salduba.util.files import resolveDir
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(os.path.join(_tr, "resources/logging.yaml")))
_logger = logging.getLogger(__name__)


def repos(db: TradingDB) -> Tuple[ContractRepo, OrderRepo, MovementRepo]:
  dnc_repo = DeltaNeutralContractRepo(db)
  c_repo = ContractRepo(db, dnc_repo)
  orderStRepo = OrderStatusRepo(db)
  sdTRepo = SoftDollarTierRepo(db)
  o_repo = OrderRepo(db, sdTRepo, orderStRepo)
  m_repo = MovementRepo(db, c_repo, o_repo)
  return c_repo, o_repo, m_repo


@pytest.fixture
def setup_db() -> TradingDB:
  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  tmp_file_path = tmp_file.name
  _logger.info(f"Database File at: {tmp_file_path}")
  schemata = resolveDir("salduba/ib_tws_proxy/backing_db/schema")
  seed_data = resolveDir("salduba/ib_tws_proxy/backing_db/seed-data")
  if not schemata or not seed_data:
    raise Exception("Schema or Seed Data directories not found")
  db_config = DbConfig(
    {
      "path": tmp_file_path,
      "schemas": schemata,
      "seed_data": seed_data,
      "expected_version": "0",
      "target_version": "1",
      "version_date": "2024-02-01 00:00:00.000",
    }
  )
  db = TradingDB(db_config)
  db.configure()
  return db


@pytest.mark.tws
def test_place_orders(setup_db: TradingDB) -> None:
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  probe_all = InputParser.input_rows_from(probeFile)
  contract_repo, order_repo, movement_repo = repos(setup_db)
  underTest = CorvinoApp(
    contract_repo,
    contract_repo.deltaNeutralContractsRepo,
    movement_repo,
    order_repo,
    appFamily=1000,
    host="localhost",
    port=7497,
  )

  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  output_file_path = "debug_output.csv"  # tmp_file.name
  _logger.info(f"DB at {setup_db.config.storage}")
  _logger.info(f"Output file at: {output_file_path}")
  assert probe_all is not None
  probe = probe_all[0:2]

  missing_contracts: Optional[list[InputRow]] = \
    underTest.lookup_contracts_for_input_rows(probe, output_file=output_file_path, ttl=10000)

  if not missing_contracts:
    result = underTest.place_orders(
      probe,
      batch=f"TestBatch_{datetime.datetime.now().timestamp()}",
      output_file=output_file_path,
    )
    assert f"{len(probe)} Movements Placed" == result, result
  else:
    assert False, f"Could not find all contracts, output at: {output_file_path}"
