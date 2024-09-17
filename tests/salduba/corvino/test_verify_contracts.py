import logging
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import Engine, create_engine

from salduba.common.persistence.alchemy.db import Db
from salduba.common.persistence.alchemy.repo import RecordBase
from salduba.corvino.io.parse_input import InputParser
from salduba.corvino.persistence.movement_record import MovementRecordOps
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecordOps, DeltaNeutralContractOps
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecordOps
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(os.path.join(_tr, "resources/logging.yaml")))
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
_logger = logging.getLogger(__name__)


@pytest.fixture
def setup_db() -> Db:
  temp = tempfile.NamedTemporaryFile()
  file_name = Path(temp.name)
  temp.close()
  print(f"##### Db file in {file_name.absolute()}")
  engine: Engine = create_engine(f"sqlite:///{file_name.absolute()}", echo=True)
  RecordBase.metadata.create_all(engine)
  return Db(engine)


def test_on_empty_db(setup_db: Db) -> None:
  # _, dnc_repo, contract_repo, order_repo, movement_repo = all_repos()
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  underTest = CorvinoApp(
    db=setup_db,
    contract_repo=ContractRecordOps(),
    dnc_repo=DeltaNeutralContractOps(),
    movements_repo=MovementRecordOps(),
    order_repo=OrderRecordOps(),
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
  with setup_db.for_work() as uow:
    result = underTest.verify_contracts_for_input_rows(probe, uow)
    probeDF = pd.read_csv(probeFile)  # pyright: ignore
    assert len(probeDF) == len(result.unknown)


@pytest.mark.tws
def test_lookup_contracts(setup_db: Db) -> None:
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  probe = InputParser.input_rows_from(probeFile)
  assert probe is not None

  underTest = CorvinoApp(
    db=setup_db,
    contract_repo=ContractRecordOps(),
    dnc_repo=DeltaNeutralContractOps(),
    movements_repo=MovementRecordOps(),
    order_repo=OrderRecordOps(),
    appFamily=100,
    host="localhost",
    port=7497,
  )

  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  output_file_path = tmp_file.name + '.xlsx'
  _logger.info(f"Output file at: {output_file_path}")
  with setup_db.for_work() as uow:
    result = underTest.lookup_contracts_for_input_rows(probe[0:10], uow=uow, ttl=10000)
    # probeDF = pd.read_csv(probeFile)
    if result.unknown:
      result.write_xlsx(output_file_path)
    assert not result.unknown, f"All Contracts should have been found. Not found[{len(result.unknown)}]: See:{output_file_path}"
