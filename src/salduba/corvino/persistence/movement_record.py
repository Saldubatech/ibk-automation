import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.record import Record
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo

_logger = logging.getLogger(__name__)


class MovementStatus(StrEnum):
    NEW = "New"
    SUBMITTED = "Submitted"
    CONFIRMED = "Confirmed"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    API_ERROR = "Error"

    @classmethod
    def fromIbk(cls, ibk_order_status: str) -> "MovementStatus":
        # https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#a27ec36f07dff982f50968c8a8887d676
        match ibk_order_status:
            case "PendingSubmit":
                return MovementStatus.SUBMITTED
            case "PendingCancel":
                return MovementStatus.CONFIRMED
            case "PreSubmitted":
                return MovementStatus.CONFIRMED
            case "Submitted":
                return MovementStatus.CONFIRMED
            case "Cancelled":
                return MovementStatus.CANCELLED
            case "Filled":
                return MovementStatus.COMPLETED
            case "Inactive":
                return MovementStatus.CANCELLED
            case _:
                return MovementStatus.API_ERROR


@dataclass
class MovementRecord(Record):
    status: MovementStatus
    batch: str
    ticker: str
    trade: int
    nombre: str
    symbol: str
    raw_type: str
    ibk_type: SecType
    country: Country
    currency: Currency
    exchange: Exchange
    exchange2: Optional[Exchange]
    contract_fk: str
    order_fk: Optional[str]


class MovementRepo(Repo[MovementRecord]):
    def __init__(self, db: TradingDB, contract_repo: ContractRepo, order_repo: OrderRepo) -> None:
        super().__init__(db, MovementRecord, "MOVEMENT")
        self.contract_repo = contract_repo
        self.order_repo = order_repo
        self.batchClause: str = "(batch = ?)"
        self.tickerClause: str = "(ticker = ?)"
        self.secTypeClause: str = "(ibk_type = ?)"
        self.exchangeClause: str = "(exchange = ?)"
        self.symbolClause: str = "(symbol = ?)"

    def forBatch(self, batch: str) -> list[MovementRecord]:
        return self.select([batch], [self.batchClause])

    def doesBatchExist(self, batch: str) -> bool:
        return self.count([batch], self.batchClause) > 0

    def findOne(self, batch: str, symbol: str, secType: SecType, exchange: Exchange) -> Optional[MovementRecord]:
        return self.selectOne(
            [batch, symbol, secType, exchange],
            [
                self.batchClause,
                self.symbolClause,
                self.secTypeClause,
                self.exchangeClause,
            ],
        )
