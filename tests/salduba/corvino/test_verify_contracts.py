import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple

import pandas as pd
import pytest

from salduba.common.configuration import DbConfig
from salduba.corvino.io.parse_input import InputParser
from salduba.corvino.persistence.movement_record import MovementRepo
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo, OrderStatusRepo, SoftDollarTierRepo
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
  db_config = DbConfig(
    storage_name=tmp_file_path,
    min_required_version=1
  )
  db = TradingDB(db_config)
  db.configure()
  contract_repo, order_repo, movement_repo = repos(db)
  dnc_repo = contract_repo.deltaNeutralContractsRepo
  return db, dnc_repo, contract_repo, order_repo, movement_repo


def test_on_empty_db() -> None:
  _, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
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
  probe = InputParser.input_rows_from(probeFile)
  assert probe is not None and len(probe) > 0
  result = underTest.verify_contracts_for_input_rows(probe)
  probeDF = pd.read_csv(probeFile)  # pyright: ignore
  assert len(probeDF) == len(result.unknown)


@pytest.mark.tws
def test_lookup_contracts() -> None:
  db, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
  _logger.info(f"DB at: {db.config.storage_path}")
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  probe = InputParser.input_rows_from(probeFile)
  assert probe is not None

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
  output_file_path = tmp_file.name + '.xlsx'
  _logger.info(f"Output file at: {output_file_path}")
  result = underTest.lookup_contracts_for_input_rows(probe[0:10], ttl=10000)
  # probeDF = pd.read_csv(probeFile)
  if result.unknown:
    result.write_xlsx(output_file_path)
  assert not result.unknown, f"All Contracts should have been found. Not found[{len(result.unknown)}]: See:{output_file_path}"
