from typing import Optional
import logging
import datetime
import time
from uuid import uuid4

from ibapi.common import ListOfContractDescription
from ibapi.contract import ContractDescription
from ibapi.contract import Contract


from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.model import ContractRecordStatus, contractCompanion, deltaNeutralCompanion
from salduba.ib_tws_proxy.backing_db.model import ContractRecord
from salduba.ib_tws_proxy.operations import Response, SuccessResponse
from salduba.ib_tws_proxy.proxy_base import ProxyBase


class SymbolUpdater(ProxyBase):
  def __init__(self, db: TradingDB, symbols: list[str], searchDelay: int = 1) -> None:
    ProxyBase.__init__(self)
    self.db = db
    self.symbols: list[str] = symbols
    self.searchDelay = searchDelay
  # Requests

  def doIt(self) -> None:
    logging.info(f"Checking {len(self.symbols)} symbols")
    for s in self.symbols:
      self.findContractDetails(s.upper())
      time.sleep(self.searchDelay)

  def findContractDetails(self, name: str) -> Optional[Response]:
    oid: int = self.tracker.nextOpId()
    now = datetime.datetime.now().timestamp()
    with self.db.cursor() as crs:
      condition = f"""
                   where
                  UPPER(symbol) like ?
                  and (expires_on is null or expires_on > ?)
                  and {ContractRecord.nominalClause};
              """
      rows = crs.execute(contractCompanion.counter + condition, (name, now)).fetchall()
      if rows[0] == 0:
        self.reqMatchingSymbols(oid, name)
      elif rows[0] > 1:
        raise Exception(f"Found more than one CONFIRMED contract record for {name} with expiration later than {now}")

  # Callback
  def symbolSamples(self, reqId: int,
                    contractDescriptions: ListOfContractDescription) -> None:   # type: ignore
    self.tracker.complete(SuccessResponse(reqId))
    descriptions: list[ContractDescription] = contractDescriptions
    now = int(datetime.datetime.now().timestamp() * 1000)
    for cd in descriptions:
      d: Contract = cd.contract
      if not d.exchange:
        d.exchange = d.primaryExchange  # Should this be 'SMART'?
      # This is here only for clarity. lists are enough for `hydrate`
      delta_neutral_contract = {
        'id': uuid4(),
        'at': now,
        'conid': d.deltaNeutralContract.conId,
        'delta': d.deltaNeutralContract.delta,
        'price': d.deltaNeutralContract.price
      } if d.deltaNeutralContract else None
      contract_record = {
        'id': uuid4(),
        'at': now,
        'expires_on': now + 3*30*24*3600*1000,
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
      with self.db.cursor() as crs:
        if delta_neutral_contract:
          dnc_values = [delta_neutral_contract[f] for f in deltaNeutralCompanion.all_fields]
          crs.execute(deltaNeutralCompanion.inserter, dnc_values)
        contract_values = [contract_record[f] for f in contractCompanion.all_fields]
        crs.execute(contractCompanion.inserter, contract_values)
    if self.tracker.isIdle():
      self.stop("Tracker is Idle")
