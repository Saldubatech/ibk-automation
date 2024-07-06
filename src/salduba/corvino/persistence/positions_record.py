import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from salduba.corvino.persistence.movement_record import MovementRecord, MovementRepo
from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.record import Record
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo
from salduba.ib_tws_proxy.domain.enumerations import SecType
from salduba.util.time import millis_epoch


@dataclass
class PositionRecord(Record):
  last_update_batch: str
  ticker: str
  last_trade: int
  symbol: str
  ibk_type: SecType
  contract_fk: str
  movement_fk: str
  obsolete: bool


class PositionRepo(Repo[PositionRecord]):
  def __init__(self, db: TradingDB, contract_repo: ContractRepo, movement_repo: MovementRepo) -> None:
    super().__init__(db, PositionRecord, "POSITIONS")
    self.contract_repo = contract_repo
    self.movement_repo = movement_repo
    self._log = logging.getLogger(self.__class__.__name__)
    self.symbol_clause = "('symbol' = ?)"
    self.sec_type_clause = "('ibk_type' = ?)"
    self.contract_clause = "('contract_fk' = ?)"

  def findOne(self, symbol: str, ibk_type: SecType, contract_fk: str, at: Optional[int] = None) -> Optional[PositionRecord]:
    return self.selectLast([symbol, ibk_type, contract_fk],
                           [self.symbol_clause, self.sec_type_clause, self. contract_clause],
                           at=at)

  def updatePosition(self, movement: MovementRecord) -> PositionRecord:
    previous = self.findOne(movement.symbol, movement.ibk_type, movement.contract_fk)
    new_record = PositionRecord(
      str(uuid4()),
      millis_epoch(),
      movement.batch,
      movement.ticker,
      movement.trade,
      movement.symbol,
      movement.ibk_type,
      movement.contract_fk,
      movement.rid,
      False)
    with self.db as db:
      with db.cursor():
        self.insert([new_record])
        if previous:
          previous.obsolete = True
          self.update(previous)
    return new_record
