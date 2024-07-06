import datetime
import logging
from typing import Optional

from ibapi.contract import Contract, DeltaNeutralContract

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.contracts.model import ContractRecord, DeltaNeutralContractRecord
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType

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


class DeltaNeutralContractRepo(Repo[DeltaNeutralContractRecord]):
  def __init__(self, db: TradingDB):
    super().__init__(db, DeltaNeutralContractRecord, "delta_neutral_contract")


def contractFromRecord(record: ContractRecord, dnc_r: Optional[DeltaNeutralContractRecord] = None) -> Contract:
  contract: Contract = Contract()
#  contract.expires_on = record.expires_on
  contract.conId = record.conId
  contract.symbol = record.symbol
  contract.secType = record.secType
  contract.lastTradeDateOrContractMonth = record.lastTradeDateOrContractMonth if record.lastTradeDateOrContractMonth else ''
  contract.strike = record.strike
  contract.right = record.right if record.right else ''
  contract.multiplier = record.multiplier if record.multiplier else ''
  contract.exchange = record.exchange
  contract.currency = record.currency
  contract.localSymbol = record.localSymbol if record.localSymbol else ''
  contract.primaryExchange = record.primaryExchange
  contract.tradingClass = record.tradingClass if record.tradingClass else ''
  contract.includeExpired = record.includeExpired
  contract.secIdType = record.secIdType if record.secIdType else ''
  contract.secId = record.secId if record.secId else ''
  contract.comboLegsDescrip = record.combo_legs_description if record.combo_legs_description else ''
  if dnc_r:
    dnc = DeltaNeutralContract()
    dnc.conId = dnc_r.conid
    dnc.delta = dnc_r.delta
    dnc.price = dnc_r.price
    contract.deltaNeutralContract = dnc
  return contract


class ContractRepo(Repo[ContractRecord]):
  contract_shelf_life = 3 * 30 * 24 * 3600 * 1000

  def __init__(self, db: TradingDB, deltaNeutralContractRepo: DeltaNeutralContractRepo) -> None:
    super().__init__(db, ContractRecord, "CONTRACT")
    self.deltaNeutralContractsRepo = deltaNeutralContractRepo
    self.expiresAfterClause: str = "(expires_on is null or expires_on > ?)"
    self.symbolClause: str = "(UPPER(symbol) = UPPER(?))"
    self.secTypeClause: str = "(sec_type = ?)"
    self.conidClause: str = "(con_id = ?)"
    self.currencyClause: str = "(currency = ?)"
    self.exchangeClause: str = "(exchange = ?)"

  def findNominalContract(
    self,
    symbol: str,
    ibk_type: str,
    exchange: str,
    alternate_exchange: Optional[str],
    currency: str,
    atTime: int,
  ) -> Optional[ContractRecord]:
    conditions = [
      self.expiresAfterClause,
      self.symbolClause,
      self.secTypeClause,
      self.exchangeClause if alternate_exchange is None else f"({self.exchangeClause} or {self.exchangeClause})",
      self.currencyClause
    ]
    parameters = [atTime, symbol, str(ibk_type), str(exchange)] + \
      ([str(alternate_exchange)] if alternate_exchange is not None else []) + \
      [str(currency)]
    _logger.debug(f"Lookup Symbol {symbol} with conditions {conditions} and parameters {parameters}")
    found: list[ContractRecord] = self.select(parameters, conditions)
    _logger.debug(f"\t With Result: {found}")
    if found and len(found) > 1:
      _logger.error(f"\tMore than one ContractRecord found for {symbol} at {exchange}:\n\t{found}")
      raise Exception(f"Found more than one NOMINAL contract record for {symbol} with expiration later than {atTime}")
    return found[0] if found else None

  def registerUpdate(self, updated: ContractRecord) -> ContractRecord:
    at: int = int(datetime.datetime.now().timestamp() * 1000)
    preExisting = self.findNominalContract(
      updated.symbol, updated.secType, updated.exchange, updated.primaryExchange, updated.currency, at
    )
    if preExisting:
      preExisting.at = at
      with self.db as db:
        with db.cursor():
          self.update(preExisting)
          updated.expires_on = at + ContractRepo.contract_shelf_life
          updated.at = at
          self.insert([updated])
    return updated
