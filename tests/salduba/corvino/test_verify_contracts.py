import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple

import pandas as pd
import pytest

from salduba.corvino.parse_input import InputParser
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


def all_repos() -> Tuple[TradingDB, DeltaNeutralContractRepo, ContractRepo, OrderRepo, MovementRepo]:
  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  tmp_file_path = tmp_file.name
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
  contract_repo, order_repo, movement_repo = repos(db)
  dnc_repo = contract_repo.deltaNeutralContractsRepo
  return db, dnc_repo, contract_repo, order_repo, movement_repo


def test_on_empty_db() -> None:
  db, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
  probe = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  underTest = CorvinoApp(
    contract_repo,
    dnc_repo,
    movement_repo,
    order_repo,
    appFamily=100,
    host="localhost",
    port=7497,
  )

  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  output_file_path = tmp_file.name
  _logger.info(f"Output file at: {output_file_path}")
  df = InputParser.read_csv(probe)
  result = underTest.verify_contracts_for_dataframe(df, output_file_path)
  probeDF = pd.read_csv(probe)
  results = pd.read_csv(output_file_path)
  assert len(probeDF) == len(results)
  assert (len(result) if result is not None else 0) == len(results)


@pytest.mark.tws
def test_lookup_contracts() -> None:
  db, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
  _logger.info(f"DB at: {db.config.storage}")
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  probe = InputParser.read_csv(probeFile)
  underTest = CorvinoApp(
    contract_repo,
    dnc_repo,
    movement_repo,
    order_repo,
    appFamily=100,
    host="localhost",
    port=7497,
  )

  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  output_file_path = tmp_file.name
  _logger.info(f"Output file at: {output_file_path}")
  result = underTest.lookup_contracts(probe[0:10], output_file=output_file_path, ttl=10000)
  # probeDF = pd.read_csv(probeFile)
  assert result is None or len(result) == 0, f"All Contracts should have been found. Not found[{len(result)}]: {result}"
