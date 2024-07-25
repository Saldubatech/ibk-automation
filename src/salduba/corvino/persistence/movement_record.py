import logging
from enum import StrEnum
from typing import Callable, Iterable, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salduba.common.persistence.alchemy.db import UnitOfWork
from salduba.common.persistence.alchemy.repo import RecordBase, RepoOps
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecord2
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord2

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


class MovementRecord2(RecordBase):
  __tablename__: str = 'MOVEMENT'
  status: Mapped[MovementStatus] = mapped_column(Enum(MovementStatus), nullable=False)
  batch: Mapped[str] = mapped_column(String(255), nullable=False)
  ticker: Mapped[str] = mapped_column(String(255), nullable=False)
  trade: Mapped[int] = mapped_column(Integer, nullable=False)
  nombre: Mapped[str] = mapped_column(String(255), nullable=False)
  symbol: Mapped[str] = mapped_column(String(255), nullable=False)
  raw_type: Mapped[str] = mapped_column(String(255), nullable=False)
  ibk_type: Mapped[SecType] = mapped_column(Enum(SecType), nullable=False)
  country: Mapped[Country] = mapped_column(Enum(Country), nullable=False)
  currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
  exchange: Mapped[Exchange] = mapped_column(Enum(Exchange), nullable=False)
  exchange2: Mapped[Optional[Exchange]] = mapped_column(Enum(Exchange), nullable=True)
  contract_fk: Mapped[str] = mapped_column(String(255), ForeignKey('CONTRACT.rid'), nullable=False)
  contract: Mapped[ContractRecord2] = \
    relationship(ContractRecord2, uselist=False, cascade='none', foreign_keys=[contract_fk], lazy=True)
  order_fk: Mapped[str] = mapped_column(String(255), ForeignKey('ORDER_T.rid'), nullable=False)
  order: Mapped[OrderRecord2] = \
    relationship(OrderRecord2, uselist=False, cascade='none', foreign_keys=[order_fk], lazy=True)


class MovementRecordOps(RepoOps[MovementRecord2]):
  def __init__(self) -> None:
    super().__init__(MovementRecord2)

  def find_for_batch(self, batch: str) -> Callable[[UnitOfWork], Iterable[MovementRecord2]]:
    return self.find(lambda q: q.where(MovementRecord2.batch == batch))

  def does_batch_exists(self, batch: str) -> Callable[[UnitOfWork], bool]:
    return lambda uow: self.count(lambda q: q.where(MovementRecord2.batch == batch))(uow) > 0

  def find_it(self, batch: str, symbol: str, sec_type: SecType, exchange: Exchange)\
      -> Callable[[UnitOfWork], Optional[MovementRecord2]]:
    return self.find_one(lambda q: q.where(
      and_(
        MovementRecord2.batch == batch,
        MovementRecord2.symbol == symbol,
        MovementRecord2.ibk_type == sec_type,
        MovementRecord2.exchange == exchange
      )
    ))
