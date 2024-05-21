import datetime
import logging
from decimal import Decimal
from typing import Any, Optional, Tuple
from uuid import uuid4

import pandas as pd
from ibapi.contract import Contract, ContractDetails, DeltaNeutralContract
from ibapi.order import Order
from ibapi.order_state import OrderState

from salduba.corvino.movements import Movement
from salduba.corvino.persistence.movement_record import MovementRepo, MovementStatus
from salduba.ib_tws_proxy.contracts.contract_repo import ContractKey, ContractRepo, DeltaNeutralContractRepo, contractFromRecord
from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.ib_tws_proxy.contracts.model import ContractRecord, DeltaNeutralContractRecord
from salduba.ib_tws_proxy.domain.enumerations import Action, Exchange, OrderTif, OrderType
from salduba.ib_tws_proxy.domain.ibapi.AvailableAlgoParams import AvailableAlgoParams
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
) -> Optional[Order]:
  """
  See: https://docs.google.com/spreadsheets/d/1pmFZ79c6chsPgXl_YJel3_k_0iu04KiPCioYGRCZFyo/edit#gid=0

  For interpretation of fields and values to assign.
  """
  order: Order = Order()
  # Because of Incompatibilties between API's
  order.eTradeOnly = False
  order.firmQuoteOnly = False

  # Regular fill-ins
  order.orderId = orderId
  order.solicited = False
  order.action = Action.BUY if trade > 0 else Action.SELL
  order.totalQuantity = Decimal(abs(trade))
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
    self.order_repo = order_repo
    self.app_family = appFamily * 100

  def _findNContract(self, r: pd.Series, at: int) -> Optional[ContractRecord]:  # type: ignore
    rs = self.contract_repo.findNominalContract(
      r["Symbol"],
      str(r["IbkType"]),
      str(r["Exchange"]),
      str(r["Exchange2"]),
      str(r["Currency"]),
      at,
    )
    return rs

  def verify_contracts_for_dataframe(
    self,
    df: pd.DataFrame,
    output_file: Optional[str] = "missing_contracts.csv",
  ) -> Optional[pd.DataFrame]:
    # TODO This is an n+1 Query that should be optimized.
    nowT = datetime.datetime.now()
    df["is_missing"] = df.apply(
      lambda r: self._findNContract(r, millis_epoch(nowT)) is None,
      axis=1,
    )
    missing: pd.DataFrame = df[df["is_missing"]]
    if output_file and len(missing) > 0:
      missing.to_csv(output_file)
    return missing if len(missing) > 0 else None

  @staticmethod
  def contract_pattern_for(r: dict[str, Any]) -> Contract:
    return ContractKey(
      r["Symbol"],
      r["IbkType"],
      r["Exchange"],
      r["Exchange2"],
      r["Currency"]
    ).contractPattern()

  def lookup_contracts(
    self,
    inputDF: pd.DataFrame,
    output_file: Optional[str] = "missing_contracts.csv",
    ttl: int = ninety_days
  ) -> Optional[pd.DataFrame]:
    nowT = datetime.datetime.now()
    _logger.debug(f"Looking for {len(inputDF)} contracts at {nowT}")
    missing: Optional[pd.DataFrame] = self.verify_contracts_for_dataframe(inputDF, output_file)
    if missing is not None and len(missing) > 0:
      _logger.debug(f"Found {len(missing)} contracts to refresh at {nowT}")
      targets = missing.apply(CorvinoApp.contract_pattern_for, axis=1)
      _logger.debug(f"\tTransformed into {len(targets)} contract Keys")
      updater: LookupContractDetails = LookupContractDetails(
        targets.to_list(),
        postProcess=lambda contract, details: self._doSaveContractRecord(ttl, contract, details),
        host=self.host,
        port=self.port,
        clientId=self.app_family + 1,
        timeout=len(targets) + 15,
        search_delay=0.1
      )
      updater.activate()
      errors = updater.wait_for_me()
      if not errors:
        missing = self.verify_contracts_for_dataframe(inputDF, output_file)
        if missing is not None and len(missing) > 0:
          _logger.warning(f"Lookup Incomplete, missing[{len(missing)}]: {missing['Ticker']}")
          return missing
        else:
          _logger.debug(f"Lookup Contracts is Done, missing: {len(missing) if missing else 0}")
          return missing
      else:
        _logger.error(f"Lookup completed with Errors: {errors}")
        return None
    else:
      _logger.debug(f"No missing contracts found at {nowT}")
      return None

  def _doSaveContractRecord(
    self,
    ttl: int,
    contract: Contract,
    details: list[dict[str, ContractDetails]],
  ) -> None:
    nowT = millis_epoch()
    _logger.debug(f"Saving Contract: {contract.symbol}::{contract.exchange}::{contract.currency} at {nowT}")
    if len(details) == 1:
      cd: ContractDetails = details[0]["contractDetails"]
      c = cd.contract
      dnc: DeltaNeutralContract = c.deltaNeutralContract
      dnc_r = (
        DeltaNeutralContractRecord(
          str(uuid4()),
          nowT,
          (nowT + ttl),  # type: ignore
          dnc.conId,
          dnc.delta,
          dnc.price
        )
        if dnc
        else None
      )
      cr = ContractRecord(
        str(uuid4()),
        nowT,
        nowT + ttl,
        c.conId,
        c.symbol,
        c.secType,
        c.lastTradeDateOrContractMonth,
        c.strike,
        c.right,
        c.multiplier,
        c.exchange,
        c.primaryExchange,
        c.currency,
        c.localSymbol,
        c.tradingClass,
        c.secIdType,
        c.secId,
        c.comboLegsDescrip,
        dnc_r.rid if dnc_r else None,
        c.includeExpired
      )
      if dnc_r:
        self.dnc_repo.insert([dnc_r])
      self.contract_repo.insert([cr])
    else:
      _logger.warning(f"More than one ContractDetails obtained for {contract.symbol}")

  def newMovement(
    self,
    batch: str,
    at: int,
    r: pd.Series,  # type: ignore
    overrideExchange: Optional[Exchange] = None,
  ) -> Tuple[Movement, Contract]:
    contractRecord: Optional[ContractRecord] = self.contract_repo.findNominalContract(
      r["Symbol"],
      r["IbkType"],
      r["Exchange"],
      r["Exchange2"],
      r["Currency"],
      at,
    )
    if contractRecord:
      dncRecord = self.dnc_repo.findById(contractRecord.delta_neutral_contract_fk)  # type: ignore
      contract = contractFromRecord(contractRecord, dncRecord)
      movement = Movement.fromDFRow(batch, r, contractRecord.rid)
      if overrideExchange:
        contract.exchange = overrideExchange
        movement.exchange = overrideExchange
        movement.exchange2 = None
      return movement, contract
    else:
      msg = f"No contract found for {r['Symbol']}, {r['Exchange']} in {batch}"
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
    movementRecord = self.movements_repo.findOne(batch, contract.symbol, contract.secType, contract.exchange)
    if movementRecord:
      movementRecord.status = MovementStatus.fromIbk(orderState.status)
      movementRecord.at = millis_epoch()
      self.movements_repo.update(movementRecord)
      return OpenOrderResponse(orderId, contract, orderRecord.toOrder())
    else:
      msg = f"No movement found for {contract.symbol}, {contract.exchange} in {batch}"
      _logger.error(msg)
      raise Exception(msg)

  def placeOrders(
    self,
    inputDF: pd.DataFrame,
    batch: Optional[str] = None,
    output_file: Optional[str] = "missing_contracts.csv",
  ) -> str:
    nowT = datetime.datetime.now()
    if batch is None:
      batch = CorvinoApp.batch_name(nowT)
    missing = self.verify_contracts_for_dataframe(inputDF, output_file)
    if missing is not None:
      return f"Not all contracts are available for movements in batch: {batch}. See {output_file} for missing contracts"
    else:
      # error: Argument 3 to "newMovement" of "CorvinoApp" has incompatible type "tuple[Hashable, Series[Any]]";
      # expected "Series[Any]"

      # m: list[Tuple[Movement, Contract]] = [
      #   self.newMovement(batch, millis_epoch(nowT), r, Exchange.SMART) for r in inputDF.iterrows() # type: ignore
      # ]

      # error: Type argument "tuple[Movement, Any]" of "Series" must be a subtype of
      # "str | bytes | date | time | bool | int | float | complex | ExtensionDtype | str | dtype[generic] | type[str] |
      # type[complex] | type[bool] | type[object] | datetime | timedelta | Period | Interval[Any] | CategoricalDtype |
      # BaseOffset"
      movements: pd.Series[Tuple[Movement, Contract]] = inputDF.apply(  # type: ignore
        lambda r: self.newMovement(batch, millis_epoch(nowT), r, Exchange.SMART),
        axis=1,
      )
      _logger.debug(f"Setting up Movements for {len(movements)} Orders")
      self.movements_repo.insert([m[0].newRecord() for m in movements])
      contractOrders: list[Tuple[Contract, Order]] = [
        (
          c,
          newOrder(
            trade=m.trade,
            conId=c.conId,
            orderRef=m.batch + "::" + m.ticker,
          ),
        )
        for m, c in movements.values
      ]
      assert all([c.exchange == Exchange.SMART for c, o in contractOrders])
      _logger.debug(f"The contractOrders: {[(c.symbol, c.exchange, o.totalQuantity, o.eTradeOnly) for c, o in contractOrders]}")
      ordering: PlaceOrders = PlaceOrders(
        targets=contractOrders,
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
      errors = ordering.wait_for_me()
      if errors:
        return f"Errors[{len(errors)}] in placing orders: {errors}"
      return f"{len(movements)} Movements Placed"
