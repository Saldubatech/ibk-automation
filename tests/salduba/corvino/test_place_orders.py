import datetime
import logging
import os
import tempfile
from pathlib import Path

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


@pytest.mark.tws
def test_place_orders(setup_db: Db) -> None:
  probeFile = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
  probe_all = InputParser.input_rows_from(probeFile)
  underTest = CorvinoApp(
    db=setup_db,
    contract_repo=ContractRecordOps(),
    dnc_repo=DeltaNeutralContractOps(),
    movements_repo=MovementRecordOps(),
    order_repo=OrderRecordOps(),
    appFamily=1000,
    host="localhost",
    port=7497,
  )

  tmp_file = tempfile.NamedTemporaryFile()
  tmp_file.close()
  output_file_path = "debug_output.csv"  # tmp_file.name
  _logger.info(f"DB at {setup_db.engine.url}")
  _logger.info(f"Output file at: {output_file_path}")
  assert probe_all is not None
  probe = probe_all[0:2]

  with setup_db.for_work() as uow:
    missing_contracts = \
      underTest.lookup_contracts_for_input_rows(probe, uow=uow, ttl=10000)

    if not missing_contracts.unknown:
      result = underTest.place_orders(
        probe,
        batch=f"TestBatch_{datetime.datetime.now().timestamp()}",
        execute_trades=False,
        uow=uow
      )
      assert f"{len(probe)} Movements Placed" == result.message, result
    else:
      assert False, f"Could not find all contracts, output at: {output_file_path}"
