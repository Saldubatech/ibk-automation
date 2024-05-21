import logging
import os
import tempfile
from pathlib import Path
from typing import Tuple

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
_tr = "tests"
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


def test_lookup_contracts() -> None:
  _, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
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
  result = underTest.lookup_contracts(probe, output_file=output_file_path, ttl=10000)
  # probeDF = pd.read_csv(probeFile)
  assert result is None, f"All Contracts should have been found. Not found[{len(result)}]: {result}"


if __name__ == "__main__":
  print("RUNNING LOOKUP CONTRACTS")
  test_lookup_contracts()
