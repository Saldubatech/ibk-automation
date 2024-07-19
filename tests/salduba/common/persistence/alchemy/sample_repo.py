import logging
from typing import List, Optional

from sqlalchemy import Engine, Float, ForeignKey, Insert, Integer, ScalarResult, String, and_, insert, or_, select
# from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from salduba.common.persistence.alchemy.repo import EntityBase, Repo
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType
from salduba.util.time import millis_epoch

# from sqlalchemy.schema import CreateTable


_logger: logging.Logger = logging.getLogger(__name__)

# reg = registry()


class DeltaNeutralContractRecord(EntityBase):
  __tablename__ = 'delta_neutral_contract'

  conid: Mapped[String] = mapped_column(Integer, nullable=False)
  delta: Mapped[float] = mapped_column(Float, nullable=False)
  price: Mapped[float] = mapped_column(Float, nullable=False)
  # default = None is just for the dataclass constructor so that a value it is not explicitly needed
  contract_fk: Mapped[str] = mapped_column(ForeignKey("contract.rid"))
  # Only needed if back-navigation in python code is needed. It does not change the schema.
  contract: Mapped['ContractRecordAlch'] = relationship(default=None, back_populates='delta_neutral_contracts')


class ContractRecordAlch(EntityBase):
  __tablename__ = 'contract'

  expires_on: Mapped[int] = mapped_column(Integer, nullable=False)
  conid: Mapped[int] = mapped_column(Integer, nullable=False)
  symbol: Mapped[str] = mapped_column(String(255), nullable=False)
  ibk_type: Mapped[SecType] = mapped_column(String(255), nullable=False)
  exchange: Mapped[Exchange] = mapped_column(String(255), nullable=False)
  primary_exchange: Mapped[Optional[Exchange]] = mapped_column(String(255), nullable=True)
  currency: Mapped[Currency] = mapped_column(String(255), nullable=False)
  delta_neutral_contracts: Mapped[List['DeltaNeutralContractRecord']] = relationship(
    default_factory=list, back_populates='contract', cascade='delete, delete-orphan'
  )
  # Optional fields/columns must be given a default, otherwise they are not optional in the constructor.
  local_symbol: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)
  trading_class: Mapped[Optional[str]] = mapped_column(String, nullable=True, default=None)


# if __name__ == '__main__':
  # cr = ContractRecord("asdf", 12345, 88898, 9797, "Symbol")
  # local_symbol is optional (it has a default), so it needs to be provided as kwarg.
  # cr2 = ContractRecord("asdf", 12345, 88898, 9797, "Symbol", local_symbol="LocalSymbol")
  # print(f"Table for Contract: {CreateTable(ContractRecord.__table__).compile(dialect=sqlite.dialect())}")
  # print(f"Table for DNC: {CreateTable(DeltaNeutralContractRecord.__table__).compile(dialect=sqlite.dialect())}")


class ContractRepo(Repo[ContractRecordAlch]):
  contract_shelf_life = 3 * 30 * 24 * 3600 * 1000

  def __init__(self, engine: Engine) -> None:
    super().__init__(engine)

  def findNominalContract(
      self,
      symbol: str,
      ibk_type: SecType,
      exchange: Exchange,
      alternate_exchange: Optional[Exchange],
      currency: Currency,
      atTime: int) -> Optional[ContractRecordAlch]:
    exchange_clause = \
      ContractRecordAlch.exchange == exchange if alternate_exchange is None \
      else or_(ContractRecordAlch.exchange == exchange, ContractRecordAlch.exchange == alternate_exchange)
    stmt = select(ContractRecordAlch).where(
      and_(
        ContractRecordAlch.expires_on > atTime,
        ContractRecordAlch.symbol == symbol,
        ContractRecordAlch.ibk_type == ibk_type,
        exchange_clause,
        ContractRecordAlch.currency == currency
      )
    )
    with Session(self.engine) as ss:
      _logger.debug(f"Lookup Symbol {symbol}")
      rs: ScalarResult[ContractRecordAlch] = ss.scalars(stmt)
      found = rs.fetchall()
      _logger.debug(f"\t With Result: {found}")
      if found and len(found) > 1:
          _logger.error(f"\tMore than one ContractRecord found for {symbol} at {exchange}:\n\t{found}")
          raise Exception(f"Found more than one NOMINAL contract record for {symbol} with expiration later than {atTime}")
      else:
        return found[0] if found else None

  def recordClz(self) -> type[ContractRecordAlch]:
    return ContractRecordAlch

  def insertStmt(self) -> Insert:
    return insert(ContractRepo)

  def registerUpdate(self, updated: ContractRecordAlch) -> ContractRecordAlch:
    at: int = millis_epoch()
    with Session(self.engine) as ss:
      preExisting = self.findNominalContract(
        updated.symbol, updated.ibk_type, updated.exchange, updated.primary_exchange, updated.currency, at
      )
      if preExisting:
        preExisting.at = at  # set the time of update
        self.update(preExisting)
      updated.expires_on = at + ContractRepo.contract_shelf_life
      updated.at = at
      self.insert([updated])
      ss.commit()
    return updated
