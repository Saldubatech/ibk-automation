# -*- coding: utf-8 -*-
# import datetime
import datetime
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

# from salduba.common.configuration import DbConfig
from salduba.common.persistence.alchemy.db import Db
from salduba.common.persistence.alchemy.repo import RecordBase
from salduba.corvino.persistence.movement_record import MovementRecord2
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecord2, ContractRecordOps, DeltaNeutralContractRecord2
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord2, OrderStatusRecord2, SoftDollarTierRecord2

# from uuid import uuid4


# from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecord2, ContractRecordOps, DeltaNeutralContractOps
# from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType

expected_db_version = 1
expected_tables = set(
  [n.__tablename__.upper() for n in [
    DeltaNeutralContractRecord2,
    ContractRecord2,
    MovementRecord2,
    SoftDollarTierRecord2,
    OrderRecord2,
    OrderStatusRecord2
    ]]
)
# {
#   "DB_INFO",
#   "DELTA_NEUTRAL_CONTRACT",
#   "CONTRACT",
#   "COMBO_LEG",
#   "CONTRACT_DETAIL_TAG",
#   "CONTRACT_DETAILS",
#   "MOVEMENT",
#   "ORDER_T"
# }


@pytest.fixture
def setup_db() -> Db:
  temp = tempfile.NamedTemporaryFile()
  file_name = Path(temp.name)
  temp.close()
  print(f"##### Db file in {file_name.absolute()}")
  engine: Engine = create_engine(f"sqlite:///{file_name.absolute()}", echo=True)
  RecordBase.metadata.create_all(engine)
  return Db(engine)


@pytest.fixture
def setup_engine() -> Engine:
  temp = tempfile.NamedTemporaryFile()
  file_name = Path(temp.name)
  temp.close()
  print(f"##### Db file in {file_name.absolute()}")
  engine: Engine = create_engine(f"sqlite:///{file_name.absolute()}", echo=True)
  RecordBase.metadata.create_all(engine)
  return engine


def test_raw_engine(setup_engine: Engine) -> None:
  with Session(setup_engine) as session:
      q = text("SELECT name FROM sqlite_master WHERE type='table';")
      rs = session.execute(q).scalars().fetchall()
      result = set(n.upper() for n in rs)
      probe = [n.upper() for n in expected_tables if n.upper() not in result]
      assert not probe, f"Retrieved Tables should include probe: {result}"


def test_db_wrapper(setup_db: Db) -> None:
  with setup_db.for_work() as uow:
    with uow.in_unit() as s:
      q = text("SELECT name FROM sqlite_master WHERE type='table';")
      rs = s.execute(q).scalars().fetchall()
      result = set(n.upper() for n in rs)
      probe = [n.upper() for n in expected_tables if n.upper() not in result]
      assert not probe, f"Retrieved Tables should include probe: {result}"


def test_contract_record(setup_db: Db) -> None:
  probe = ContractRecord2(
    rid=str(uuid4()),
    at=int(datetime.datetime.now().timestamp() * 1000),
    expires_on=1111,
    con_id=12345,
    symbol="SYMBOL",
    sec_type=SecType.STK,
    last_trade_date_or_contract_month="March",
    strike=77.88,
    right="RIGHT",
    multiplier="MULTI",
    lookup_exchange=Exchange.SMART,
    exchange=Exchange.SMART,
    currency=Currency.USD,
    local_symbol="L_SYMBOL",
    primary_exchange=Exchange.NYSE,
    trading_class="TR_CLASS",
    sec_id_type="SEC_ID_TYPE",
    sec_id="SEC_ID",
    combo_legs_description="COMBO_LEGS_DESC",
    delta_neutral_contract=None,
    include_expired=True
   )
  repo = ContractRecordOps()

  with setup_db.for_work() as uow:
    repo.insert_one(probe)(uow)
    rs = list(repo.find()(uow))
    assert len(rs) == 1, "Should have only one record: {}".format(rs)
    assert rs[0].__dict__ == probe.__dict__, "Values should match"
