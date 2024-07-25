# import datetime
import logging
from typing import Callable, Optional

from ibapi.contract import Contract, DeltaNeutralContract  # pyright: ignore
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salduba.common.persistence.alchemy.db import UnitOfWork
from salduba.common.persistence.alchemy.repo import RecordBase, RepoOps
# from salduba.ib_tws_proxy.backing_db.db import TradingDB
# from salduba.ib_tws_proxy.backing_db.repo import Repo
# from salduba.ib_tws_proxy.contracts.model import ContractRecord, DeltaNeutralContractRecord
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType
from salduba.util.time import millis_epoch

_logger = logging.getLogger(__name__)


class ContractKey:

  @staticmethod
  def resolveContractExchange(exchange: Exchange, exchange2: Optional[Exchange]) -> Exchange:
    if exchange == Exchange.ISLAND:
      match exchange2:
        case None:
          return Exchange.NYSE
        case Exchange.UNKNOWN:
          return Exchange.NYSE
        case Exchange.NONE:
          return Exchange.NYSE
        case _:
          return exchange2
    else:
      return exchange

  def __init__(
    self,
    symbol: str,
    secType: SecType,
    exchange: Exchange,
    exchange2: Optional[Exchange],
    currency: Currency,
  ):
    self.symbol = symbol
    self.secType = secType
    self.exchange = ContractKey.resolveContractExchange(exchange, exchange2)
    self.currency = currency

  def contractPattern(self) -> Contract:
    contract = Contract()
    contract.symbol = self.symbol
    contract.secType = self.secType
    contract.exchange = self.exchange
    contract.currency = self.currency
    return contract


class DeltaNeutralContractRecord2(RecordBase):
  __tablename__: str = "delta_neutral_contract"
  con_id: Mapped[int] = mapped_column(Integer, nullable=False)
  delta: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

  def to_dnc(self) -> DeltaNeutralContract:
    dnc = DeltaNeutralContract()
    dnc.conId = self.con_id
    dnc.delta = self.delta
    dnc.price = self.price
    return dnc


class DeltaNeutralContractOps(RepoOps[DeltaNeutralContractRecord2]):
  def __init__(self) -> None:
    super().__init__(DeltaNeutralContractRecord2)


class ContractRecord2(RecordBase):
  __tablename__: str = 'CONTRACT'

  expires_on: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  con_id: Mapped[int] = mapped_column(Integer, nullable=False)
  symbol: Mapped[str] = mapped_column(String(255), nullable=False)
  sec_type: Mapped[SecType] = mapped_column(Enum(SecType), nullable=False)
  last_trade_date_or_contract_month: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  strike: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  right: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  multiplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  lookup_exchange: Mapped[Exchange] = mapped_column(Enum(Exchange), nullable=False)
  exchange: Mapped[Exchange] = mapped_column(Enum(Exchange), nullable=False)
  primary_exchange: Mapped[Exchange] = mapped_column(Enum(Exchange), nullable=False)
  currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)
  local_symbol: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  trading_class: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  sec_id_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  sec_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  combo_legs_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  include_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
  delta_neutral_contract_fk: Mapped[Optional[str]] = \
    mapped_column(String(255), ForeignKey("delta_neutral_contract.rid"), nullable=True)
  delta_neutral_contract: Mapped[Optional[DeltaNeutralContractRecord2]] = \
    relationship(
      DeltaNeutralContractRecord2,
      foreign_keys=[delta_neutral_contract_fk],
      uselist=False,
      single_parent=True,
      cascade="all, delete-orphan",
      lazy=True)

  def to_contract(self) -> Contract:
    contract: Contract = Contract()
  #  contract.expires_on = record.expires_on
    contract.conId = self.con_id
    contract.symbol = self.symbol
    contract.secType = self.sec_type
    contract.lastTradeDateOrContractMonth = \
      self.last_trade_date_or_contract_month if self.last_trade_date_or_contract_month else ''
    contract.strike = self.strike
    contract.right = self.right if self.right else ''
    contract.multiplier = self.multiplier if self.multiplier else ''
    contract.exchange = self.exchange
    contract.currency = self.currency
    contract.localSymbol = self.local_symbol if self.local_symbol else ''
    contract.primaryExchange = self.primary_exchange
    contract.tradingClass = self.trading_class if self.trading_class else ''
    contract.includeExpired = self.include_expired
    contract.secIdType = self.sec_id_type if self.sec_id_type else ''
    contract.secId = self.sec_id if self.sec_id else ''
    contract.comboLegsDescrip = self.combo_legs_description if self.combo_legs_description else ''
    if self.delta_neutral_contract:
      contract.deltaNeutralContract = self.delta_neutral_contract.to_dnc()  # pyright: ignore
    return contract


class ContractRecordOps(RepoOps[ContractRecord2]):
  def __init__(self) -> None:
    super().__init__(ContractRecord2)

  def find_nominal_contract(
    self,
    symbol: str,
    ibk_type: SecType,
    exchange: Exchange,
    alternate_exchange: Optional[Exchange],
    currency: Currency,
    atTime: int,
  ) -> Callable[[UnitOfWork], Optional[ContractRecord2]]:
    return self.find_one(
      lambda q: q.where(
        and_(
          ContractRecord2.expires_on > atTime,
          ContractRecord2.symbol == symbol,
          ContractRecord2.sec_type == ibk_type,
          (ContractRecord2.exchange.in_([exchange, alternate_exchange]) if alternate_exchange
           else (ContractRecord2.exchange == exchange)),
          ContractRecord2.currency == currency
          )
      )
    )

  def register_update(self, updated: ContractRecord2) -> Callable[[UnitOfWork], ContractRecord2]:
    def rs(uow: UnitOfWork) -> ContractRecord2:
      at: int = millis_epoch()
      pre_existing = self.find_nominal_contract(
        updated.symbol,
        updated.sec_type,
        updated.exchange,
        updated.primary_exchange,
        updated.currency, at)(uow)
      if pre_existing:
        pre_existing.at = at
      return updated
    return rs
