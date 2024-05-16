from typing import Self, Optional
import logging

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.model import db_version
from salduba.ib_tws_proxy.backing_db.record import RecordMeta, Record
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo
from salduba.ib_tws_proxy.domain.enumerations import SecType, Exchange
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo

_logger = logging.getLogger(__name__)

movementCompanion = RecordMeta(
  'MOVEMENT',
  # Natural Key: (batch, ticker)
  [
    'status',  # StrEnum
    'batch',
    'ticker',
    'trade',
    'nombre',
    'symbol',
    'raw_type',
    'country',
    'ibk_type',
    'currency',
    'exchange',
    'exchange2',
    'contract_fk',
    'order_fk'
  ],
  db_version
)


class MovementRecord(Record):
  batchClause = '(batch = ?)'
  tickerClause = '(ticker = ?)'
  secTypeClause = '(secType = ?)'
  exchangeClause = '(exchange = ?)'
  symbolClause = '(symbol = ?)'


  @classmethod
  def hydrate(cls, *argsv) -> Self:  # type: ignore
    return cls(argsv[0], argsv[1], *argsv[2:])  # type: ignore


  def __init__(self, rid: str, at: int, *args) -> None:
    super().__init__(rid, at, movementCompanion, *args)


class MovementRepo(Repo[RecordMeta, MovementRecord]):

  def __init__(self, db: TradingDB, contract_repo: ContractRepo, order_repo: OrderRepo) -> None:
    super().__init__(db, movementCompanion, MovementRecord.hydrate)
    self.contract_repo = contract_repo
    self.order_repo = order_repo

  def forBatch(self, batch: str) -> list[MovementRecord]:
    return self.select([batch], [MovementRecord.batchClause])

  def doesBatchExist(self, batch: str):
    return self.count([batch], MovementRecord.batchClause) > 0

  def findOne(self, batch: str, symbol: str, secType: SecType, exchange: Exchange) -> Optional[MovementRecord]:
    return self.selectOne(
      [batch, symbol, secType, exchange],
      [MovementRecord.batchClause,
       MovementRecord.symbolClause,
       MovementRecord.secTypeClause,
       MovementRecord.exchangeClause]
    )
