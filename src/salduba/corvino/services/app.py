import datetime
import logging
from typing import Optional, Tuple
from uuid import uuid4

from ibapi.contract import Contract, ContractDetails, DeltaNeutralContract  # pyright: ignore
from ibapi.order import Order  # pyright: ignore
from ibapi.order_state import OrderState  # pyright: ignore

from salduba.corvino.io.parse_input import InputRow
from salduba.corvino.io.results_out import ResultsBatch
from salduba.corvino.movements import Movement
from salduba.corvino.persistence.movement_record import MovementRepo, MovementStatus
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo, contractFromRecord
from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.ib_tws_proxy.contracts.model import ContractRecord, DeltaNeutralContractRecord
from salduba.ib_tws_proxy.domain.enumerations import Action, Currency, Exchange, OrderTif, OrderType, SecType
from salduba.ib_tws_proxy.domain.ibapi.AvailableAlgoParams import AvailableAlgoParams
from salduba.ib_tws_proxy.operations import ErrorResponse
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord, OrderRepo
from salduba.ib_tws_proxy.orders.placing_orders import OpenOrderResponse, OrderResponse, PlaceOrderPostProcessor, PlaceOrders
from salduba.util.time import millis_epoch, ninety_days

_logger = logging.getLogger(__name__)
_logger.info(f"Logging to: {__name__}")


def newOrder(
  trade: int,
  conId: int,
  orderRef: str = "",
  transmit: bool = False,
  orderId: Optional[int] = None,
) -> Order:
  """
  See: https://docs.google.com/spreadsheets/d/1pmFZ79c6chsPgXl_YJel3_k_0iu04KiPCioYGRCZFyo/edit#gid=0

  For interpretation of fields and values to assign.
  """
  order: Order = Order()
  # Because of Incompatibilities between API's
  order.eTradeOnly = False
  order.firmQuoteOnly = False

  # Regular fill-ins
  order.orderId = orderId if orderId else 0
  order.solicited = False
  order.action = Action.BUY if trade > 0 else Action.SELL
  order.totalQuantity = int(abs(trade))
  order.orderType = OrderType.MKT
  # order.lmtPrice: float = 0.0
  order.tif = OrderTif.DAY
  # order.ocaGroup = ""
  # order.ocaType: int = 0
  order.orderRef = orderRef
  order.transmit = transmit
  # order.parentId: int = 0
  order.blockOrder = False
  order.sweepToFill = False
  # order.displaySize = None
  # order.triggerMethod = 0
  order.outsideRth = False
  order.hidden = False
  # order.goodAfterTime: str = None
  # order.goodTillDate: str = None
  order.overridePercentageConstraints = False
  # order.rule80A = None
  # order.allOrNone = False ???
  # order.minQty: int = ???
  # order.percentOffset = 0.0
  # order.trailStopPrice = 0.0
  # order.trailingPercent = 0.0
  # order.faGroup = ""
  # order.faMethod = ""
  # order.openClose = "OPEN"
  # order.origin = 0
  # order.shortSaleSlot = 0
  # order.designatedLocation = ""
  # order.exemptCode = 0
  # order.discretionaryAmt = 0
  order.optOutSmartRouting = False
  # order.auctionStrategy = 0
  # order.startingPrice = 0.0
  # order.stockRefPrice = 0.0
  # order.delta = 0.0
  # order.stockRangeLower = 0.0
  # order.volatility = 0.0
  # order.volatilityType = 0
  # order.continuousUpdate = False
  # order.referencePriceType = 0
  # order.deltaNeutralAuxPrice = 0.0
  # order.deltaNeutralConId = 0
  # order.deltaNeutralClearingAccount = ""
  # order.deltaNeutralClearingIntent = ""
  # order.deltaNeutralOpenClose = ""
  # order.deltaNeutralShortSale = False
  # order.deltaNeutralDesignatedLocation = ""
  # order.basisPoints = 0.0
  # order.basisPointsType = 0
  # order.scaleInitLevelSize = 0
  # order.scaleSubsLevelSize = 0
  # order.scalePriceIncrement = 0.0
  # order.scalePriceAdjustValue = 0.0
  # order.scalePriceAdjustInterval = 0
  # order.scaleProfitOffset = 0.0
  # order.scaleAutoReset = False
  # order.scaleInitPosition = 0
  # order.scaleInitFillQty = 0
  # order.scaleRandomPercent = False
  # order.hedgeType = ""
  # order.hedgeParam = ""
  # order.account = ""
  # order.settlingFirm = ""
  # order.clearingAccount = ""
  # order.clearingIntent = ""
  AvailableAlgoParams.FillAdaptiveParams(baseOrder=order, priority="Patient")
  # Not needed, added in the `FillAdaptiveParams` call
  #  order.algoStrategy = AlgoStrategy.ADAPTIVE
  #  order.algoParams = []
  order.whatIf = False
  order.algoId = ""
  # order.notHeld = False
  # order.smartComboRoutingParams = None
  # order.orderComboLegs = None
  # order.orderMiscOptions = None
  # order.activeStartTime = ""
  # order.activeStopTime = ""
  # order.scaleTable = ""
  # order.modelCode = ""
  # order.extOperator = ""
  # order.cashQty = 0.0
  # order.mifid2DecisionMaker = ""
  # order.mifid2DecisionAlgo = ""
  # order.mifid2ExecutionTrader = ""
  # order.mifid2ExecutionAlgo = ""
  # order.dontUseAutoPriceForHedge = False
  # order.autoCancelDate = ""
  # order.filledQuantity = Decimal(0.0)
  # order.refFuturesConId = 0
  # order.autoCancelParent = False
  # order.shareholder = ""
  # order.imbalanceOnly = False
  # order.routeMarketableToBbo = False
  # order.parentPermId = 0
  # order.advancedErrorOverride = ""
  # order.manualOrderTime = ""
  # order.minTradeQty = 0
  # order.minCompeteSize = 0
  # order.competeAgainstBestOffset = False
  # order.midOffsetAtWhole = 0.0
  # order.midOffsetAtHalf = 0.0
  # order.randomizeSize = False
  # order.randomizePrice = False
  order.referenceContractId = conId
  # order.isPeggedChangeAmountDecrease = False
  # order.peggedChangeAmount = 0.0
  # order.referenceChangeAmount = 0.0
  # order.referenceExchangeId = ""
  # order.adjustedOrderType = ""
  # order.triggerPrice = 0.0
  # order.lmtPriceOffset = 0.0
  # order.adjustedStopPrice = 0.0
  # order.adjustedStopLimitPrice = 0.0
  # order.adjustedTrailingAmount = 0.0
  # order.adjustableTrailingUnit = 0
  # order.conditions = []
  # order.conditionsIgnoreRth = False
  # order.conditionsCancelOrder = False
  # order.softDollarTier = ???
  # order.isOmsContainer = False
  # order.discretionaryUpToLimitPrice = False
  # order.usePriceMgmtAlgo = None
  # order.duration = 0
  # order.postToAts = 0
  return order


class CorvinoApp:
  @staticmethod
  def batch_name(nowT: datetime.datetime) -> str:
    nowStr = nowT.strftime("%Y%m%d%H%M%S")
    return f"movement_batch_{nowStr}"

  def __init__(
    self,
    contract_repo: ContractRepo,
    dnc_repo: DeltaNeutralContractRepo,
    movements_repo: MovementRepo,
    order_repo: OrderRepo,
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
    self.contract_repo = contract_repo
    self.dnc_repo = dnc_repo
    self.movements_repo = movements_repo
    self.host = host
    self.port = port
    self.order_repo: OrderRepo = order_repo
    self.app_family = appFamily * 100

  def _findNominalContract(self, r: InputRow, at: int) -> Optional[ContractRecord]:
    rs = self.contract_repo.findNominalContract(
      r.symbol,
      r.ibk_type,
      r.exchange,
      None if r.exchange2 == Exchange.NONE else r.exchange2,
      r.currency,
      at)
    return rs

  def verify_contracts_for_input_rows(self, input_rows: list[InputRow]) -> ResultsBatch:
    nowT = datetime.datetime.now()
    input_dict = {r.ticker: r for r in input_rows}
    finding = {r.ticker: self._findNominalContract(r, millis_epoch(nowT)) for r in input_rows}
    found_contracts: list[ContractRecord] = list(filter(None, finding.values()))
    missing_rows: list[InputRow] = [input_dict[t] for t in finding.keys() if finding[t] is None]
    # missing_rows = [r for r in input_rows if self._findNominalContract(r, millis_epoch(nowT)) is None]
    # if output_file and missing_rows:
    #   missing = [
    #     {
    #       "ticker" : m.ticker,
    #       "symbol" : m.symbol,
    #       "exchange" : m.exchange,
    #       "exchange2" : m.exchange2,
    #       "currency" : m.currency,
    #       "country" : m.country
    #     } for m in missing_rows]
    #   missingDf = pd.DataFrame(missing)
    #   missingDf.to_csv(output_file)
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
                                      ttl: int = ninety_days) -> ResultsBatch:
    nowT = datetime.datetime.now()
    _logger.debug(f"Looking for {len(input_rows)} contracts at {nowT}")
    verification: ResultsBatch = self.verify_contracts_for_input_rows(input_rows)
    if not verification.unknown:
      return verification
    else:
      _logger.debug(f"Found {len(verification.unknown)} contracts to refresh at {nowT}")
      targets = self._prepareContractsForLookup(verification.unknown)
      _logger.debug(f"\tTransformed into {len(targets)} contract Keys")
      errors: dict[str, list[ErrorResponse]] | None = self._doLookups(targets, ttl)
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
        lookup_result = self.verify_contracts_for_input_rows(input_rows)
        updated = [r for r in lookup_result.known if filter(lambda cr : cr.rid == r.rid, verification.known)]
        return ResultsBatch(
          nowT,
          f"Lookup Incomplete, missing[{len(lookup_result.unknown)}]" if lookup_result.unknown else "Lookup Complete, no missing",
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

  def _doLookups(self, targets: dict[str, tuple[Contract, InputRow]], ttl: int) -> Optional[dict[str, list[ErrorResponse]]]:
    updater: LookupContractDetails = LookupContractDetails(
      [c for (c, _) in targets.values()],
      postProcess=lambda c, details:
        self._doSaveContractRecord(
          ttl,
          targets[f"{c.symbol}::{c.exchange}"][1], c, details
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
  ) -> None:
    nowT = millis_epoch()
    _logger.debug(f"Saving Contract: {contract.symbol}::{contract.exchange}::{contract.currency} at {nowT}")
    if len(details) == 1:
      cd: ContractDetails = details[0]["contractDetails"]
      c = cd.contract
      dnc: Optional[DeltaNeutralContract] = c.deltaNeutralContract if c.deltaNeutralContract else None
      dnc_r = (
        DeltaNeutralContractRecord(
          str(uuid4()),
          nowT,
          dnc.conId,
          dnc.delta,
          dnc.price
        ) if dnc else None
      )
      cr = ContractRecord(
        str(uuid4()),
        nowT,
        expires_on=nowT + ttl,
        conId=c.conId,
        symbol=c.symbol,
        secType=SecType(c.secType),
        lastTradeDateOrContractMonth=c.lastTradeDateOrContractMonth,
        strike=c.strike,
        right=c.right,
        multiplier=c.multiplier,
        lookup_exchange=Exchange(c.exchange),
        exchange=ir.exchange,
        primaryExchange=Exchange(c.primaryExchange),
        currency=Currency(c.currency),
        localSymbol=c.localSymbol,
        tradingClass=c.tradingClass,
        secIdType=c.secIdType,
        secId=c.secId,
        combo_legs_description=c.comboLegsDescrip,
        delta_neutral_contract_fk=dnc_r.rid if dnc_r else None,
        includeExpired=c.includeExpired
      )
      if dnc_r:
        self.dnc_repo.insert([dnc_r])
      self.contract_repo.insert([cr])
    else:
      _logger.warning(f"More than one ContractDetails obtained for {contract.symbol}")

  def new_movement(self,
                   batch: str,
                   at: int,
                   r: InputRow,
                   override_exchange: Optional[Exchange] = None) -> Tuple[Movement, Contract]:
    contract_record: Optional[ContractRecord] = self._findNominalContract(r, at)
    if contract_record:
      dnc_record: Optional[DeltaNeutralContractRecord] = self.dnc_repo.findById(
        contract_record.delta_neutral_contract_fk
        ) if contract_record.delta_neutral_contract_fk else None
      contract: Contract = contractFromRecord(contract_record, dnc_record)
      movement = Movement.from_input_row(batch, r, contract_record)
      if override_exchange:
        contract.exchange = override_exchange
        movement.exchange = override_exchange
        movement.exchange2 = None
      return movement, contract
    else:
      msg = f"No contract found for {r.symbol}, {r.exchange} in {batch}"
      _logger.error(msg)
      raise Exception(msg)

  def postPlaceOrderForBatch(self, batch: str) -> PlaceOrderPostProcessor:
    return lambda orderId, contract, orderRecord, orderState: (
      self.postPlaceOrder(batch, orderId, contract, orderRecord, orderState)
    )

  def postPlaceOrder(
    self,
    batch: str,
    orderId: int,
    contract: Contract,
    orderRecord: OrderRecord,
    orderState: OrderState,
  ) -> OrderResponse:
    movementRecord = \
      self.movements_repo.findOne(batch, contract.symbol, SecType(contract.secType), Exchange(contract.exchange))
    if movementRecord:
      movementRecord.status = MovementStatus.fromIbk(orderState.status)
      movementRecord.at = millis_epoch()
      self.movements_repo.update(movementRecord)
      return OpenOrderResponse(orderId, contract, orderRecord.toOrder())
    else:
      msg = f"No movement found for {contract.symbol}, {contract.exchange} in {batch}"
      _logger.error(msg)
      raise Exception(msg)

  def place_orders(
    self,
    input_rows: list[InputRow],
    batch: Optional[str] = None,
    execute_trades: bool = False
  ) -> ResultsBatch:
    nowT = datetime.datetime.now()
    if batch is None:
      batch = CorvinoApp.batch_name(nowT)
    missing = self.verify_contracts_for_input_rows(input_rows)

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
      contractOrders: list[tuple[Contract, Order]] = self._prepare_orders(batch, nowT, input_rows, execute_trades)
      errors = self._order_placement(batch, contractOrders)
      movements_for_batch = self.movements_repo.findForBatch(batch)
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

  def _prepare_orders(
      self, batch: str, nowT: datetime.datetime, input_rows: list[InputRow], execute_trades: bool
      ) -> list[tuple[Contract, Order]]:

    def movementMapper(r: InputRow) -> tuple[Movement, Contract]:
      return self.new_movement(batch, millis_epoch(nowT), r, Exchange.SMART)

    movements: list[tuple[Movement, Contract]] = [movementMapper(ir) for ir in input_rows]

    _logger.debug(f"Setting up Movements for {len(movements)} Orders")
    self.movements_repo.insert([m[0].newRecord() for m in movements])
    contractOrders: list[Tuple[Contract, Order]] = [
      (c, newOrder(m.trade, c.conId, orderRef=m.batch + "::" + m.ticker, transmit=execute_trades)) for m, c in movements
    ]
    assert all([c.exchange == Exchange.SMART for c, _ in contractOrders])
    _logger.debug(f"The contractOrders: {[(c.symbol, c.exchange, o.totalQuantity, o.eTradeOnly) for c, o in contractOrders]}")
    return contractOrders

  def _order_placement(
      self, batch: str, contract_orders: list[tuple[Contract, Order]]) -> Optional[dict[str, list[ErrorResponse]]]:
    ordering: PlaceOrders = PlaceOrders(
      targets=contract_orders,
      orderRepo=self.order_repo,
      contractRepo=self.contract_repo,
      postProcess=self.postPlaceOrderForBatch(batch),
      host=self.host,
      port=self.port,
      clientId=self.app_family + 1,
      timeout=len(contract_orders) + 15,
      delay=None,
    )
    ordering.activate()
    return ordering.wait_for_me()
