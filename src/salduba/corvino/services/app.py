import datetime
import logging
from typing import Optional
from uuid import uuid4

from ibapi.contract import Contract, ContractDetails, DeltaNeutralContract  # pyright: ignore
from ibapi.order_state import OrderState  # pyright: ignore

from salduba.common.persistence.alchemy.db import Db, UnitOfWork
from salduba.corvino.io.parse_input import InputRow
from salduba.corvino.io.results_out import ResultsBatch
from salduba.corvino.persistence.movement_record import MovementRecord2, MovementRecordOps, MovementStatus
from salduba.ib_tws_proxy.contracts.contract_repo import (
    ContractRecord2,
    ContractRecordOps,
    DeltaNeutralContractOps,
    DeltaNeutralContractRecord2,
)
from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.ib_tws_proxy.domain.enumerations import Currency, Exchange, SecType
from salduba.ib_tws_proxy.operations import ErrorResponse
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord2, OrderRecordOps, newOrderRecord
from salduba.ib_tws_proxy.orders.placing_orders import OpenOrderResponse, OrderResponse, PlaceOrderPostProcessor, PlaceOrders
from salduba.util.time import millis_epoch, ninety_days

_logger = logging.getLogger(__name__)
_logger.info(f"Logging to: {__name__}")


class CorvinoApp:
  @staticmethod
  def batch_name(nowT: datetime.datetime) -> str:
    nowStr = nowT.strftime("%Y%m%d%H%M%S")
    return f"movement_batch_{nowStr}"

  def __init__(
    self,
    db: Db,
    contract_repo: ContractRecordOps,
    dnc_repo: DeltaNeutralContractOps,
    movements_repo: MovementRecordOps,
    order_repo: OrderRecordOps,
    appFamily: int,
    host: str = "localhost",
    port: int = 7497,
  ) -> None:
    """

    :param contract_repo:
    :param dnc_repo:
    :param movements_repo:
    :param order_repo:
    :param appFamily: Each family will be multiplied by 100
      and use the range from 0 to 99 for clientId of this application
    :param host:
    :param port:
    """
    self.db = db
    self.contract_repo = contract_repo
    self.dnc_repo = dnc_repo
    self.movements_repo = movements_repo
    self.host = host
    self.port = port
    self.order_repo = order_repo
    self.app_family = appFamily * 100

  def _findNominalContract(self, r: InputRow, at: int, uow: UnitOfWork) -> Optional[ContractRecord2]:
    rs = self.contract_repo.find_nominal_contract(
      r.symbol, r.ibk_type,
      r.exchange,
      None if r.exchange2 == Exchange.NONE else r.exchange2,
      r.currency,
      at)(uow)
    return rs

  def verify_contracts_for_input_rows(self, input_rows: list[InputRow], uow: UnitOfWork) -> ResultsBatch:
    nowT = datetime.datetime.now()
    input_dict = {r.ticker: r for r in input_rows}
    finding: dict[str, Optional[ContractRecord2]] = {
      r.ticker: self._findNominalContract(r, millis_epoch(nowT), uow) for r in input_rows
    }
    found_contracts: list[ContractRecord2] = [v for v in finding.values() if v is not None]
    missing_rows: list[InputRow] = [input_dict[t] for t in finding.keys() if finding[t] is None]
    return ResultsBatch(
      atTime=nowT,
      message="All contracts already known" if not missing_rows else "Some contracts not known",
      inputs=input_rows,
      known=found_contracts,
      updated=[],
      movements_placed=[],
      unknown=missing_rows if missing_rows else [],
      errors={}
    )

  def lookup_contracts_for_input_rows(self,
                                      input_rows: list[InputRow],
                                      uow: UnitOfWork,
                                      ttl: int = ninety_days) -> ResultsBatch:
    nowT = datetime.datetime.now()
    _logger.debug(f"Looking for {len(input_rows)} contracts at {nowT}")
    verification: ResultsBatch = self.verify_contracts_for_input_rows(input_rows, uow)
    if not verification.unknown:
      return verification
    else:
      _logger.debug(f"Found {len(verification.unknown)} contracts to refresh at {nowT}")
      targets = self._prepareContractsForLookup(verification.unknown)
      _logger.debug(f"\tTransformed into {len(targets)} contract Keys")
      errors: dict[str, list[ErrorResponse]] | None = self._doLookups(targets, ttl, uow)
      if (errors) and ('error' in errors) and bool(errors['error']):
        _logger.error(f"Lookup completed with Errors: {errors}")
        return ResultsBatch(
          nowT,
          "Lookup Completed with Errors",
          input_rows,
          verification.known,
          updated=[],
          unknown=verification.unknown,
          movements_placed=[],
          errors=errors
        )
      else:
        _logger.debug("Lookup completed without Errors")
        lookup_result = self.verify_contracts_for_input_rows(input_rows, uow)
        if len(lookup_result.unknown) == len(verification.unknown):
          updated: list[ContractRecord2] = []
        else:
          first_pass = set(cr.con_id for cr in verification.known)
          updated = [cr for cr in lookup_result.known if cr.con_id not in first_pass]
        return ResultsBatch(
          nowT,
          f"Lookup Incomplete, missing[{len(lookup_result.unknown)}]"
          if lookup_result.unknown else "Lookup Complete, no missing Contracts",
          input_rows,
          verification.known,
          updated=updated,
          unknown=lookup_result.unknown,
          movements_placed=[],
          errors={}
        )

  def _prepareContractsForLookup(self, missing: list[InputRow]) -> dict[str, tuple[Contract, InputRow]]:
    def populateContractForLookup(ir: InputRow) -> tuple[Contract, InputRow]:
      rs: Contract = Contract()
      rs.symbol = ir.symbol
      if ir.exchange == Exchange.ISLAND:  # ISLAND is not reliable to look up contracts, use SMART instead
        rs.exchange = Exchange.SMART
      else:
        rs.exchange = ir.exchange
      # rs.exchange = ir.exchange
      # if ir.exchange2 and ir.exchange2 != Exchange.NONE:
      #   rs.primaryExchange = ir.exchange2
      rs.secType = ir.ibk_type
      rs.currency = ir.currency
      return rs, ir
    return {f"{c.symbol}::{c.exchange}": (c, r) for (c, r) in [populateContractForLookup(r) for r in missing]}

  def _doLookups(self, targets: dict[str, tuple[Contract, InputRow]], ttl: int, uow: UnitOfWork)\
      -> Optional[dict[str, list[ErrorResponse]]]:
    updater: LookupContractDetails = LookupContractDetails(
      [c for (c, _) in targets.values()],
      postProcess=lambda c, details:
        self._doSaveContractRecord(
          ttl,
          targets[f"{c.symbol}::{c.exchange}"][1], c, details, uow
        ),
      host=self.host,
      port=self.port,
      clientId=self.app_family + 1,
      timeout=len(targets) + 15,
      search_delay=0.1
    )
    updater.activate()
    return updater.wait_for_me()

  def _doSaveContractRecord(
    self,
    ttl: int,
    ir: InputRow,
    contract: Contract,
    details: list[dict[str, ContractDetails]],
    uow: UnitOfWork
  ) -> None:
    nowT = millis_epoch()
    if len(details) == 1:
      _logger.debug(f"Saving Contract: {contract.symbol}::{contract.exchange}::{contract.currency} at {nowT}")
      cd: ContractDetails = details[0]["contractDetails"]
      c = cd.contract
      dnc: Optional[DeltaNeutralContract] = c.deltaNeutralContract if c.deltaNeutralContract else None
      dnc_r = (
        DeltaNeutralContractRecord2(
          rid=str(uuid4()),
          at=nowT,
          con_id=dnc.conId,
          delta=dnc.delta,
          price=dnc.price
        ) if dnc else None
      )
      cr = ContractRecord2(
        rid=str(uuid4()),
        at=nowT,
        expires_on=nowT + ttl,
        con_id=c.conId,
        symbol=c.symbol,
        sec_type=SecType(c.secType),
        last_trade_date_or_contract_month=c.lastTradeDateOrContractMonth,
        strike=c.strike,
        right=c.right,
        multiplier=c.multiplier,
        lookup_exchange=Exchange(c.exchange),
        exchange=ir.exchange,
        primary_exchange=Exchange(c.primaryExchange),
        currency=Currency(c.currency),
        local_symbol=c.localSymbol,
        trading_class=c.tradingClass,
        sec_id_type=c.secIdType,
        sec_id=c.secId,
        combo_legs_description=c.comboLegsDescrip,
        include_expired=c.includeExpired,
        delta_neutral_contract=dnc_r
      )
      self.contract_repo.insert_one(cr)(uow)
      _logger.debug(f"Saved Contract with symbol: {cr.symbol}")
    else:
      _logger.warning(f"More than one ContractDetails obtained for {contract.symbol}")

  def postPlaceOrderForBatch(self, batch: str) -> PlaceOrderPostProcessor:
    return lambda orderId, contract, orderRecord, orderState: (
      self.postPlaceOrder(batch, orderId, contract, orderRecord, orderState)
    )

  def postPlaceOrder(
    self,
    batch: str,
    orderId: int,
    contract: Contract,
    orderRecord: OrderRecord2,
    orderState: OrderState
  ) -> OrderResponse:
    with self.db.for_work() as uow:
      movementRecord = \
        self.movements_repo.find_it(
          batch,
          contract.symbol,
          SecType(contract.secType),
          Exchange(contract.exchange))(uow)
      if movementRecord:
        movementRecord.status = MovementStatus.fromIbk(orderState.status)
        movementRecord.at = millis_epoch()
        return OpenOrderResponse(orderId, contract, movementRecord.order.toOrder())
      else:
        msg = f"No movement found for {contract.symbol}, {contract.exchange} in {batch}"
        _logger.error(msg)
        raise Exception(msg)

  def place_orders(
    self,
    input_rows: list[InputRow],
    uow: UnitOfWork,
    batch: Optional[str] = None,
    execute_trades: bool = False
  ) -> ResultsBatch:
    nowT = datetime.datetime.now()

    if batch is None:
      batch = CorvinoApp.batch_name(nowT)
    missing = self.verify_contracts_for_input_rows(input_rows, uow)
    if missing.unknown:
      return ResultsBatch(
        nowT,
        f"Not all contracts are available for movements in batch: {batch}.",
        input_rows,
        missing.known,
        missing.updated,
        missing.unknown,
        [],
        missing.errors
        )
    else:
      movements: list[MovementRecord2] = \
        self._prepare_movements(batch, nowT, input_rows, execute_trades, uow, override_exchange=Exchange.SMART)
      self.order_repo.insert([m.order for m in movements])(uow)
      self.movements_repo.insert(movements)(uow)
      errors = self._order_placement(batch, movements)
      movements_for_batch: list[MovementRecord2] = list(self.movements_repo.find_for_batch(batch)(uow))
      if (errors) and ('error' in errors) and bool(errors['error']):
        return ResultsBatch(
          nowT,
          f"Errors[{len(errors['error'])}] trying to place orders",
          input_rows,
          missing.known,
          missing.updated,
          missing.unknown,
          movements_for_batch,
          errors)
      else:
        return ResultsBatch(
          nowT,
          f"{len(movements_for_batch)} Movements Placed",
          input_rows,
          missing.known,
          missing.updated,
          missing.unknown,
          movements_for_batch,
          missing.errors
        )

  def _prepare_movements(
      self,
      batch: str,
      nowT: datetime.datetime,
      input_rows: list[InputRow],
      execute_trades: bool,
      uow: UnitOfWork,
      override_exchange: Optional[Exchange]
      ) -> list[MovementRecord2]:
    movements: list[MovementRecord2] = []
    for r in input_rows:
      cr: Optional[ContractRecord2] = self._findNominalContract(r, at=millis_epoch(nowT), uow=uow)
      if cr:
        if override_exchange:
          cr.exchange = override_exchange
        order: OrderRecord2 = newOrderRecord(r.trade, cr.con_id,
                                             nowT=nowT, orderRef=batch + "::" + r.ticker, transmit=execute_trades)
        movement: MovementRecord2 = MovementRecord2(
            rid=str(uuid4()),
            at=millis_epoch(),
            status=MovementStatus.NEW,
            batch=batch,
            ticker=r.ticker,
            trade=r.trade,
            nombre=f"{cr.symbol}, {cr.sec_type}, {cr.local_symbol}",  # should be 'name',
            symbol=r.symbol,
            raw_type=r.raw_type,
            ibk_type=r.ibk_type,
            country=r.country,
            currency=r.currency,
            exchange=override_exchange if override_exchange else r.exchange,
            exchange2=r.exchange2,
            contract=cr,
            order=order
          )
        movements.append(movement)
      else:
        raise Exception(f"No Contract found for {r.__dict__}")
    return movements

  def _order_placement(
      self, batch: str, movements: list[MovementRecord2]) -> Optional[dict[str, list[ErrorResponse]]]:
    assert not [m for m in movements if m.order.transmit]
    ordering: PlaceOrders = PlaceOrders(
      db=self.db,
      targets=movements,
      orderRepo=self.order_repo,
      contractRepo=self.contract_repo,
      postProcess=self.postPlaceOrderForBatch(batch),
      host=self.host,
      port=self.port,
      clientId=self.app_family + 1,
      timeout=len(movements) + 15,
      delay=None,
    )
    ordering.activate()
    return ordering.wait_for_me()
