from decimal import Decimal
from typing import Optional, Tuple
import datetime
import logging
from uuid import uuid4

import pandas as pd
from ibapi.contract import Contract, ContractDetails
from ibapi.order import Order
from ibapi.order_state import OrderState

from salduba.corvino.movements import Movement, MovementStatus
from salduba.corvino.persistence.movement_record import MovementRepo
from salduba.corvino.parse_input import InputParser
from salduba.ib_tws_proxy.backing_db.model import ContractRecordStatus, ContractRecord, DeltaNeutralContractRecord
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo, ContractKey, \
  contractFromRecord
from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.ib_tws_proxy.domain.ibapi.AvailableAlgoParams import AvailableAlgoParams
from salduba.ib_tws_proxy.domain.enumerations import Action, OrderType, OrderTif
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo, OrderRecord
from salduba.ib_tws_proxy.orders.placing_orders import PlaceOrders, OrderResponse, OpenOrderResponse, \
  PlaceOrderPostProcessor
from salduba.util.time import millis_epoch, ninety_days

_logger = logging.getLogger(__name__)
_logger.info(f"Logging to: {__name__}")


def newOrder(
                     trade: int,
                     orderRef: str = '',
                     transmit: bool = False,
                     orderId: Optional[int] = None
                     ) -> Optional[Order]:
  """
  See: https://docs.google.com/spreadsheets/d/1pmFZ79c6chsPgXl_YJel3_k_0iu04KiPCioYGRCZFyo/edit#gid=0

  For interpretation of fields and values to assign.
  """
  order: Order = Order()
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
  AvailableAlgoParams.FillAdaptiveParams(
    baseOrder=order,
    priority='Patient'
  )
  # Not needed, added in the `FillAdaptiveParams` call
  #    order.algoStrategy = AlgoStrategy.ADAPTIVE
  #    order.algoParams = []
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
  # order.referenceContractId = 0
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
  def _batch_name(nowT: datetime.datetime) -> str:
    nowStr = nowT.strftime("%Y%m%d%H%M%S")
    return f"movement_batch_{nowStr}"

  def __init__(self,
               contract_repo: ContractRepo,
               dnc_repo: DeltaNeutralContractRepo,
               movements_repo: MovementRepo,
               order_repo: OrderRepo,
               appFamily: int,
               host: str = 'localhost',
               port: int = 7497) -> None:
    """

    :param contract_repo:
    :param dnc_repo:
    :param movements_repo:
    :param order_repo:
    :param appFamily: Each family will be multiplied by 100
        and use the range from 0 to 99 for client Id of this application
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

  def verify_contracts_for_csv_file(
      self,
      datafile_path: str,
      output_file='missing_contracts.csv',
      output_required: bool = True
  ) -> bool:
    df = InputParser.read_csv(datafile_path)
    return self.verify_contracts_for_dataframe(df, output_file, output_required)

  def verify_contracts_for_dataframe(
      self,
      df: pd.DataFrame,
      output_file: str = 'missing_contracts.csv',
      output_required: bool = True
  ) -> bool:
    # TODO This is an n+1 Query that should be optimized.
    df['is missing'] = df.apply(
      lambda r: self.contract_repo.findNominalContract(
        r['Symbol'],
        r['IbkType'],
        r['Exchange'],
        r['Exchange2'],
        r['Currency'],
        millis_epoch()) is None,
      axis=1)
    missing = df[df['is missing']][['Symbol', 'IbkType', 'Exchange', 'Currency']]
    missing_check = len(missing) > 0
    if output_required and missing_check:
      missing.to_csv(output_file)
    return not missing_check

  def lookup_contracts(
      self,
      movementsDF: pd.DataFrame,
      output_file: str = 'missing_contracts.csv',
      ttl: int = ninety_days
  ) -> bool:
    nowT = datetime.datetime.now()
    verification = self.verify_contracts_for_dataframe(movementsDF, output_file, False)
    if not verification:
      movementsDF['requires_refresh'] = movementsDF.apply(
        lambda r: self.contract_repo.findNominalContract(
          r['Symbol'],
          r['IbkType'],
          r['Exchange'],
          r['Exchange2'],
          r['Currency'],
          millis_epoch(nowT)) is not None,
        axis=1)
      targets = movementsDF[movementsDF['requires_refresh'] == True].apply(
        lambda r: ContractKey(
          r['Symbol'],
          r['IbkType'],
          r['Exchange'],
          r['Exchange2'],
          r['Currency']
        ).contractPattern(),
        axis=1)
      updater: LookupContractDetails = LookupContractDetails(
        targets.tolist(),
        postProcess=lambda contract, details: self._doSaveContractRecord(ttl, contract, details),
        host=self.host,
        port=self.port,
        clientId=self.app_family+1,
        timeout=15*60,
        terminate='q'
      )
      updater.activate()
      updater.wait_for_me()
      verification = self.verify_contracts_for_dataframe(movementsDF, output_file, True)
    return verification

  def _doSaveContractRecord(self, ttl: int, contract: Contract, details: list[dict[str, ContractDetails]]) -> None:
    nowT = millis_epoch()
    if len(details) == 1:
      cd: ContractDetails = details[0]['contractDetails']
      c = cd.contract
      dnc = c.deltaNeutralContract
      dnc_r = DeltaNeutralContractRecord(
        str(uuid4()),
        nowT,
        (nowT+ttl),
        dnc.conId,
        dnc.delta,
        dnc.price
      ) if dnc else None
      cr = ContractRecord(
        str(uuid4()),
        nowT,
        nowT+ttl,
        ContractRecordStatus.NOMINAL,
        c.conId,
        c.symbol,
        c.secType,
        c.lastTradeDateOrContractMonth,
        c.strike,
        c.right,
        c.multiplier,
        c.exchange,
        c.currency,
        c.localSymbol,
        c.primaryExchange,
        c.tradingClass,
        c.includeExpired,
        c.secIdType,
        c.secId,
        c.description,
        c.issuerId,
        c.comboLegsDescrip,
        dnc.id if dnc else None)
      if dnc_r:
        self.dnc_repo.insert([dnc_r])
      self.contract_repo.insert([cr])
    else:
      _logger.warning(f"More than one ContractDetails obtained for {contract.symbol}")

  def newMovement(self, batch: str, at: int, r: pd.Series) -> Tuple[Movement, Contract]:
    contractRecord = self.contract_repo.findNominalContract(
      r['Symbol'],
      r['IbkType'],
      r['Exchange'],
      r['Exchange2'],
      r['Currency'],
      at)
    if contractRecord:
      dncRecord = self.dnc_repo.findById(contractRecord.delta_neutral_contract_fk)  # type: ignore
      return Movement.fromDFRow(batch, r, contractRecord.id), contractFromRecord(contractRecord, dncRecord)
    else:
      msg = f"No contract found for {r['Symbol']}, {r['Exchange']} in {batch}"
      _logger.error(msg)
      raise Exception(msg)


  def postPlaceOrderForBatch(self, batch: str) -> PlaceOrderPostProcessor:
    return lambda orderId, contract, orderRecord, orderState: (  # type: ignore
      self.postPlaceOrder(batch, orderId, contract, orderRecord, orderState))

  def postPlaceOrder(self,
                     batch: str,
                     orderId: int,
                     contract: Contract,
                     orderRecord: OrderRecord,
                     orderState: OrderState
                     ) -> OrderResponse:
    movementRecord = self.movements_repo.findOne(batch, contract.symbol, contract.secType, contract.exchange)
    if movementRecord:
      movementRecord.status = MovementStatus.fromIbk(orderState.status)  # type: ignore
      movementRecord.at = millis_epoch()
      self.movements_repo.update(movementRecord)
      return OpenOrderResponse(orderId, contract, orderRecord.toOrder())
    else:
      msg = f"No movement found for {contract.symbol}, {contract.exchange} in {batch}"
      _logger.error(msg)
      raise Exception(msg)

  def placeOrders(self,
                  movementsDF: pd.DataFrame,
                  batch: Optional[str] = None,
                  output_file: str = 'missing_contracts.csv') -> str:
    nowT = datetime.datetime.now()
    if batch is None:
      batch = CorvinoApp._batch_name(nowT)
    verification = self.verify_contracts_for_dataframe(movementsDF, output_file, True)
    if not verification:
      return f"Not all contracts are available for movements in batch: {batch}. See {output_file} for missing contracts"
    else:
      movements = movementsDF.apply(
        f=lambda r: self.newMovement(batch, millis_epoch(nowT), r),
        axis=1
      )
      self.movements_repo.insert([m[0].newRecord() for m in movements])
      ordering: PlaceOrders = PlaceOrders(
        targets=[(c, newOrder(m.trade, m.batch + '::' + m.ticker, False)) for m, c in movements],
        orderRepo=self.order_repo,
        contractRepo=self.contract_repo,
        postProcess=self.postPlaceOrderForBatch(batch),
        host=self.host,
        port=self.port,
        clientId=self.app_family+1,
        timeout=15*60,
        terminate='q',
        delay=None
      )
      ordering.activate()
      ordering.wait_for_me()
      return f"{len(movements)} Movements Placed"
