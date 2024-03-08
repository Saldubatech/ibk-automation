from typing import Optional
import logging
import datetime
import time
from uuid import uuid4

import pandas as pd

from ibapi.common import ListOfContractDescription
from ibapi.contract import ContractDescription
from ibapi.contract import Contract


from salduba.ib_tws_proxy.backing_db.record import RecordMeta
from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.repo import Repo
from salduba.ib_tws_proxy.backing_db.model import ContractRecordStatus, DeltaNeutralContractRecord, contractCompanion, deltaNeutralCompanion
from salduba.ib_tws_proxy.backing_db.model import ContractRecord
from salduba.ib_tws_proxy.operations import Response, SuccessResponse
from salduba.ib_tws_proxy.proxy_base import ProxyBase

_logger = logging.getLogger(__name__)


def millis_epoch() -> int:
  return int(datetime.datetime.now().timestamp() * 1000)


class SymbolUpdater(ProxyBase):
  def __init__(self,
               db: TradingDB,
               symbols: list[str],
               unconfirmed_csv_path: str,
               not_found_symbols_csv_path: str,
               searchDelay: float = 0.5,
               logLevel: int = logging.INFO) -> None:
    ProxyBase.__init__(self, logLevel)
    _logger.setLevel(logLevel)
    self.db = db
    self.contracts = Repo[RecordMeta, ContractRecord](db, contractCompanion, ContractRecord.hydrate, logLevel)
    self.deltaNeutralContracts = \
      Repo[RecordMeta, DeltaNeutralContractRecord](db, deltaNeutralCompanion, DeltaNeutralContractRecord.hydrate, logLevel)
    self.symbols: list[str] = symbols
    _logger.info(f"Symbols to Process: {len(self.symbols)}")
    self.refresh_required: list[str] = self.check_refresh_required()
    _logger.info(f"Requiring Refresh: {len(self.refresh_required)}")
    self.unconfirmed_csv_path = unconfirmed_csv_path
    self.not_found_symbols_csv_path = not_found_symbols_csv_path
    self.searchDelay = searchDelay
    self.contract_shelf_life = 3*30*24*3600*1000  # 3 months * 30 days * 24 h * 3600 sec * 1000 millis
    self.requested: dict[int, str] = {}
  # Requests

  def doIt(self) -> None:
    _logger.info(f"Checking {len(self.symbols)} symbols")
    if self.isActive():
      self.fetchNextContractDetails()
    else:
      _logger.warn("Proxy Not Active...")

  def check_refresh_required(self) -> list[str]:
    return [s for s in self.symbols if not self.lookupInDb(s, millis_epoch())]

  def fetchNextContractDetails(self) -> None:
    if self.refresh_required:
      _logger.debug(f"Pending: {len(self.refresh_required)}")
      oid: Optional[int] = self.tracker.nextOpId()
      if oid:
        name = self.refresh_required.pop(0)
        self.requested[oid] = name
        _logger.info(f"> Requesting {name} from Server, to-go: {len(self.refresh_required)}")
        self.reqMatchingSymbols(oid, name)
        time.sleep(self.searchDelay)
    else:
      _logger.info("No more pending")
      if self.tracker.isIdle():
        _logger.info("Found tracker Idle")
        self.wrap_up()
        self.stop("Tracker is Idle")

  def lookupInDb(self, name: str, atTime: int) -> bool:
    result = False
    with self.db as db:
      with db.cursor() as crs:
        condition = f"""
                    where
                    {ContractRecord.expiresAfterClause}
                    and ({ContractRecord.aliasClause}
                         or {ContractRecord.descriptionClause})
                    and ({ContractRecord.statusClause}
                         or {ContractRecord.statusClause});"""
        query = contractCompanion.counter + condition
        _logger.debug(f"Lookup Symbol {name} with Query :\n {query}")
        parameters = [atTime, name, name, ContractRecordStatus.NOMINAL, ContractRecordStatus.UNCONFIRMED]
        _logger.debug(f"And Parameters: {parameters}")
        rows: list[tuple[int]] = crs.execute(query, parameters).fetchall()
        if rows and rows[0][0] == 0:
          _logger.debug("\tNot Found, will request from server")
        elif rows and rows[0][0] > 1:
          _logger.warn(f"\tMore than one ({rows[0][0]}) found for {name}")
          result = True
          # raise Exception(f"Found more than one NOMINAL contract record for {name} with expiration later than {atTime}")
        else:
          result = True
          _logger.debug(f"\tFound one: {rows}")
    return result

  # Callback
  def symbolSamples(self, reqId: int,
                    contractDescriptions: ListOfContractDescription) -> None:   # type: ignore
    alias = self.requested.get(reqId)
    if not contractDescriptions:
      _logger.warn(f"\tNo Contract Description for {self.requested.get(reqId)}")
    else:
      _logger.info(f"\tReceived Symbols for {self.requested.get(reqId)}: {contractDescriptions}")
      del (self.requested[reqId])
    self.tracker.complete(SuccessResponse(reqId))
    descriptions: list[ContractDescription] = contractDescriptions
    now = millis_epoch()
    for cd in descriptions:
      d: Contract = cd.contract
      _logger.debug(f"Processing Contract: {d}")
      if not d.exchange:
        d.exchange = d.primaryExchange  # Should this be 'SMART'?
      # This is here only for clarity. lists are enough for `hydrate`
      delta_neutral_contract = {
        'id': str(uuid4()),
        'at': now,
        'conid': d.deltaNeutralContract.conId,
        'delta': d.deltaNeutralContract.delta,
        'price': d.deltaNeutralContract.price
      } if d.deltaNeutralContract else None
      contract_record = {
        'id': str(uuid4()),
        'at': now,
        'alias': alias,
        'expires_on': now + self.contract_shelf_life,
        'status': ContractRecordStatus.NOMINAL if len(descriptions) == 1 else ContractRecordStatus.UNCONFIRMED,
        'conid': d.conId,
        'symbol': d.symbol,
        'sec_type': d.secType,
        'last_trade_date_or_contract_month': d.lastTradeDateOrContractMonth,
        'strike': d.strike,
        'right': d.right,
        'multiplier': d.multiplier,
        'exchange': d.exchange,
        'currency': d.currency,
        'local_symbol': d.localSymbol,
        'primary_exchange': d.primaryExchange,
        'trading_class': d.tradingClass,
        'include_expired': d.includeExpired,
        'sec_id_type': d.secIdType,
        'sec_id': d.secId,
        'description': d.description,
        'issuer_id': d.issuerId,
        'combo_legs_description': d.comboLegsDescrip,
        'delta_neutral_contract_fk': delta_neutral_contract['id'] if delta_neutral_contract else None
      }
      if delta_neutral_contract:
        dnc = [delta_neutral_contract[f] for f in deltaNeutralCompanion.all_fields]
        self.deltaNeutralContracts.insert_raw([dnc])
      contract_values = [contract_record[f] for f in contractCompanion.all_fields]
      _logger.debug(f"Inserting {contract_values}")
      self.contracts.insert_raw([contract_values])
    self.fetchNextContractDetails()

  def wrap_up(self) -> None:
    _logger.info("Wrapping up")
    unconfirmed = self.find_unconfirmed_contracts()
    if len(unconfirmed) > 0:
      with open(self.unconfirmed_csv_path, 'w') as file:
        unconfirmed[['alias',
                     'status',
                     'conid',
                     'symbol',
                     'sec_type',
                     'exchange',
                     'currency',
                     'local_symbol',
                     'primary_exchange',
                     'trading_class',
                     'sec_id_type',
                     'sec_id',
                     'description',
                     'issuer_id']].to_csv(file)
    if len(self.requested) > 0:
      _logger.debug(f"Missing Requests: {self.requested.values()}")
      with open(self.not_found_symbols_csv_path, 'w') as file:
        for s in self.requested.values():
          file.write(s+'\n')

  def find_unconfirmed_contracts(self) -> pd.DataFrame:
    return self.contracts.selectAsDataFrame(
      [ContractRecordStatus.UNCONFIRMED, millis_epoch()],
      ContractRecord.statusClause,
      ContractRecord.expiresAfterClause
      )  # 'status = {}'.format(ContractRecordStatus.UNCONFIRMED))
