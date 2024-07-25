import logging
from datetime import datetime
from typing import Callable, Iterable, Optional
from uuid import uuid4

from ibapi.order import Order  # pyright: ignore
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, inspect
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salduba.common.persistence.alchemy.db import UnitOfWork
from salduba.common.persistence.alchemy.repo import RecordBase, RepoOps
from salduba.ib_tws_proxy.domain.enumerations import Action, IbOrderStatus, OrderType
from salduba.ib_tws_proxy.domain.ibapi.AvailableAlgoParams import AvailableAlgoParams
from salduba.util.time import millis_epoch

_logger = logging.getLogger(__name__)


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
# @dataclass
# class OrderRecord(Record):
#   orderId: int
#   clientId: int
#   action: str
#   orderType: str
#   transmit: bool
#   permId: Optional[int] = None
#   solicited: Optional[bool] = None
#   totalQuantity: Optional[float] = None
#   lmtPrice: Optional[float] = None
#   auxPrice: Optional[float] = None
#   tif: Optional[str] = None
#   ocaGroup: Optional[str] = None
#   ocaType: Optional[int] = None
#   orderRef: Optional[str] = None
#   parentId: Optional[int] = None
#   blockOrder: Optional[bool] = None
#   sweepToFill: Optional[bool] = None
#   displaySize: Optional[int] = None
#   triggerMethod: Optional[int] = None
#   outsideRth: Optional[bool] = None
#   hidden: Optional[bool] = None
#   goodAfterTime: Optional[str] = None
#   goodTillDate: Optional[str] = None
#   overridePercentageConstraints: Optional[bool] = None
#   rule80A: Optional[str] = None
#   allOrNone: Optional[bool] = None
#   minQty: Optional[int] = None
#   percentOffset: Optional[float] = None
#   trailStopPrice: Optional[float] = None
#   trailingPercent: Optional[float] = None
#   faGroup: Optional[str] = None
#   faMethod: Optional[str] = None
#   faPercentage: Optional[str] = None
#   openClose: Optional[str] = None
#   origin: Optional[int] = None
#   shortSaleSlot: Optional[int] = None
#   designatedLocation: Optional[str] = None
#   exemptCode: Optional[int] = None
#   discretionaryAmt: Optional[float] = None
#   optOutSmartRouting: Optional[bool] = None
#   auctionStrategy: Optional[int] = None
#   startingPrice: Optional[float] = None
#   stockRefPrice: Optional[float] = None
#   delta: Optional[float] = None
#   stockRangeLower: Optional[float] = None
#   stockRangeUpper: Optional[float] = None
#   volatility: Optional[float] = None
#   volatilityType: Optional[int] = None
#   continuousUpdate: Optional[int] = None
#   referencePriceType: Optional[int] = None
#   deltaNeutralOrderType: Optional[str] = None
#   deltaNeutralAuxPrice: Optional[float] = None
#   deltaNeutralConId: Optional[int] = None
#   deltaNeutralSettlingFirm: Optional[str] = None
#   deltaNeutralClearingAccount: Optional[str] = None
#   deltaNeutralOpenClose: Optional[str] = None
#   deltaNeutralShortSale: Optional[str] = None
#   deltaNeutralShortSaleSlot: Optional[str] = None
#   deltaNeutralDesignatedLocation: Optional[str] = None
#   basisPoints: Optional[float] = None
#   basisPointsType: Optional[int] = None
#   scaleInitLevelSize: Optional[int] = None
#   scaleSubsLevelSize: Optional[int] = None
#   scalePriceIncrement: Optional[float] = None
#   scalePriceAdjustValue: Optional[float] = None
#   scalePriceAdjustInterval: Optional[int] = None
#   scaleProfitOffset: Optional[float] = None
#   scaleAutoReset: Optional[bool] = None
#   scaleInitPosition: Optional[int] = None
#   scaleInitFillQty: Optional[int] = None
#   scaleRandomPercent: Optional[bool] = None
#   hedgeType: Optional[str] = None
#   hedgeParam: Optional[str] = None
#   account: Optional[str] = None
#   settlingFirm: Optional[str] = None
#   clearingAccount: Optional[str] = None
#   clearingIntent: Optional[str] = None
#   algoStrategy: Optional[str] = None
#   whatIf: Optional[bool] = None
#   algoId: Optional[str] = None
#   notHeld: Optional[bool] = None
#   activeStartTime: Optional[str] = None
#   activeStopTime: Optional[str] = None
#   scaleTable: Optional[str] = None
#   modelCode: Optional[str] = None
#   extOperator: Optional[str] = None
#   cashQty: Optional[float] = None
#   mifid2DecisionMaker: Optional[str] = None
#   mifid2DecisionAlgo: Optional[str] = None
#   mifid2ExecutionTrader: Optional[str] = None
#   mifid2ExecutionAlgo: Optional[str] = None
#   dontUseAutoPriceForHedge: Optional[bool] = None
#   autoCancelDate: Optional[str] = None
#   filledQuantity: Optional[float] = None
#   refFuturesConId: Optional[int] = None
#   autoCancelParent: Optional[bool] = None
#   shareholder: Optional[str] = None
#   imbalanceOnly: Optional[bool] = None
#   routeMarketableToBbo: Optional[bool] = None
#   parentPermId: Optional[int] = None
#   randomizeSize: Optional[bool] = None
#   randomizePrice: Optional[bool] = None
#   referenceContractId: Optional[int] = None
#   isPeggedChangeAmountDecrease: Optional[bool] = None
#   peggedChangeAmount: Optional[float] = None
#   referenceChangeAmount: Optional[float] = None
#   adjustedOrderType: Optional[str] = None
#   triggerPrice: Optional[float] = None
#   lmtPriceOffset: Optional[float] = None
#   adjustedStopPrice: Optional[float] = None
#   conditionsIgnoreRth: Optional[bool] = None
#   conditionsCancelOrder: Optional[bool] = None
#   isOmsContainer: Optional[bool] = None
#   usePriceMgmtAlgo: Optional[bool] = None

#   def toOrder(self) -> Order:
#     result = Order()
#     rd = result.__dict__
#     for k in self.own_fields():
#       rd[k] = self.__dict__[k]
#     return result

#   @classmethod
#   def newFromOrder(cls, rid: str, at: int, order: Order) -> 'OrderRecord':
#     return cls.from_dict(rid, at, order.__dict__)


class SoftDollarTierRecord2(RecordBase):
  __tablename__: str = "SOFT_DOLLAR_TIER"
  name: Mapped[str] = mapped_column(String(255), nullable=False)
  value: Mapped[str] = mapped_column(String(255), nullable=False)
  display_name: Mapped[str] = mapped_column(String(255), nullable=False)


class SoftDollarTierOps(RepoOps[SoftDollarTierRecord2]):
  def __init__(self) -> None:
    super().__init__(SoftDollarTierRecord2)


class OrderStatusRecord2(RecordBase):
  __tablename__: str = "ORDER_STATUS"
  order_id: Mapped[int] = mapped_column(Integer, nullable=False)
  status: Mapped[IbOrderStatus] = mapped_column(Enum(IbOrderStatus), nullable=False)
  filled: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  remaining: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  avg_fill_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  perm_id: Mapped[int] = mapped_column(Integer, nullable=False)
  parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  last_fill_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
  client_id: Mapped[int] = mapped_column(Integer, nullable=False)
  why_held: Mapped[str] = mapped_column(String(255), nullable=False)
  mkt_cap_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class OrderStatusOps(RepoOps[OrderStatusRecord2]):
  def __init__(self) -> None:
    super().__init__(OrderStatusRecord2)

  def for_order(self, order_id: int) -> Callable[[UnitOfWork], Iterable[OrderStatusRecord2]]:
    return self.find(lambda q: q.where(OrderStatusRecord2.order_id == order_id))


class OrderRecord2(RecordBase):
  __tablename__: str = 'ORDER_T'
  # eTradeOnly: Mapped[bool] = mapped_column(Boolean, nullable=False)
  # firmQuoteOnly: Mapped[bool] = mapped_column(Boolean, nullable=False)
  orderId: Mapped[int] = mapped_column(Integer, nullable=False)
  clientId: Mapped[int] = mapped_column(Integer, nullable=False)
  action: Mapped[str] = mapped_column(String(length=255), nullable=False)
  orderType: Mapped[str] = mapped_column(String(length=255), nullable=False)
  transmit: Mapped[bool] = mapped_column(Boolean, nullable=False)
  permId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  solicited: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  totalQuantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  lmtPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  auxPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  tif: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  ocaGroup: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  ocaType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  orderRef: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  parentId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  blockOrder: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  sweepToFill: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  displaySize: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  triggerMethod: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  outsideRth: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  hidden: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  goodAfterTime: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  goodTillDate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  overridePercentageConstraints: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  rule80A: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  allOrNone: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  minQty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  percentOffset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  trailStopPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  trailingPercent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  faGroup: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  faMethod: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  faPercentage: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  openClose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  origin: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  shortSaleSlot: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  designatedLocation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  exemptCode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  discretionaryAmt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  optOutSmartRouting: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  auctionStrategy: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  startingPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  stockRefPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  delta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  stockRangeLower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  stockRangeUpper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  volatility: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  volatilityType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  continuousUpdate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  referencePriceType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  deltaNeutralOrderType: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralAuxPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  deltaNeutralConId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  deltaNeutralSettlingFirm: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralClearingAccount: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralOpenClose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralShortSale: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralShortSaleSlot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  deltaNeutralDesignatedLocation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  basisPoints: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  basisPointsType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scaleInitLevelSize: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scaleSubsLevelSize: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scalePriceIncrement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  scalePriceAdjustValue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  scalePriceAdjustInterval: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scaleProfitOffset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  scaleAutoReset: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  scaleInitPosition: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scaleInitFillQty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  scaleRandomPercent: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  hedgeType: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  hedgeParam: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  account: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  settlingFirm: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  clearingAccount: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  clearingIntent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  algoStrategy: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  whatIf: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  algoId: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  notHeld: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  activeStartTime: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  activeStopTime: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  scaleTable: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  modelCode: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  extOperator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  cashQty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  mifid2DecisionMaker: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  mifid2DecisionAlgo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  mifid2ExecutionTrader: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  mifid2ExecutionAlgo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  dontUseAutoPriceForHedge: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  autoCancelDate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  filledQuantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  refFuturesConId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  autoCancelParent: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  shareholder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  imbalanceOnly: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  routeMarketableToBbo: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  parentPermId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  randomizeSize: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  randomizePrice: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  referenceContractId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
  isPeggedChangeAmountDecrease: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  peggedChangeAmount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  referenceChangeAmount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  adjustedOrderType: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
  triggerPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  lmtPriceOffset: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  adjustedStopPrice: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  conditionsIgnoreRth: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  conditionsCancelOrder: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  isOmsContainer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  usePriceMgmtAlgo: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
  soft_dollar_tier_fk: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey(SoftDollarTierRecord2.rid), nullable=True)
  softDollarTier: Mapped[Optional[SoftDollarTierRecord2]] = relationship(
      SoftDollarTierRecord2,
      foreign_keys=[soft_dollar_tier_fk],
      uselist=False,
      single_parent=True,
      cascade="all, delete-orphan",
      lazy=True)
  order_status_fk: Mapped[str] = mapped_column(String(255), ForeignKey(OrderStatusRecord2.rid), nullable=False)
  order_status: Mapped[OrderStatusRecord2] = relationship(
      OrderStatusRecord2,
      foreign_keys=[order_status_fk],
      uselist=False,
      single_parent=True,
      cascade="all, delete-orphan",
      lazy=True)

  def toOrder(self) -> Order:
    result = Order()
    domain_keys = (f.key for f in inspect(OrderRecord2).columns
                   if f.key not in ['rid', 'at']
                   and not f.key.startswith('_')
                   and not f.key.endswith('_fk'))
    for k in domain_keys:
      v = self.__dict__[k]
      if v is not None:
        result.__setattr__(k, v)
    # Required b/c the interface does not support == True (Weird)
    result.eTradeOnly = False
    result.firmQuoteOnly = False
    AvailableAlgoParams.FillAdaptiveParams(baseOrder=result, priority="Patient")
    return result

  @classmethod
  def newFromOrder(cls, rid: str, at: int, order: Order) -> 'OrderRecord2':
    domain_fields = (c.key for c in inspect(OrderRecord2).columns
                     if c.key not in ['rid', 'at']
                     and not c.key.startswith('_')
                     and not c.key.endswith('_fk'))
    return cls(
      rid=rid,
      at=at,
      **{k: order.__dict__[k] for k in domain_fields}
    )


def newOrderRecord(
  trade: int,
  conId: int,
  nowT: datetime,
  orderRef: str = "",
  transmit: bool = False,
  orderId: Optional[int] = None,
) -> OrderRecord2:
  """
  See: https://docs.google.com/spreadsheets/d/1pmFZ79c6chsPgXl_YJel3_k_0iu04KiPCioYGRCZFyo/edit#gid=0

  For interpretation of fields and values to assign.
  """
  order: OrderRecord2 = OrderRecord2(
    rid=str(uuid4()),
    at=millis_epoch(nowT),
    # Because of Incompatibilities between API's
    # eTradeOnly=False,
    # firmQuoteOnly=False,

    # Regular fill-ins
    orderId=orderId if orderId else 0,
    clientId=orderId if orderId else 0,
    permId=None,
    solicited=None,
    action=Action.BUY if trade > 0 else Action.SELL,
    totalQuantity=int(abs(trade)),
    orderType=OrderType.MKT,
    lmtPrice=None,
    auxPrice=None,
    tif=None,
    ocaGroup=None,
    ocaType=None,
    orderRef=orderRef,
    transmit=transmit,
    parentId=None,
    blockOrder=None,
    sweepToFill=None,
    displaySize=None,
    triggerMethod=None,
    outsideRth=None,
    hidden=None,
    goodAfterTime=None,
    goodTillDate=None,
    overridePercentageConstraints=None,
    rule80A=None,
    allOrNone=False,
    minQty=None,
    percentOffset=None,
    trailStopPrice=None,
    trailingPercent=None,
    faGroup=None,
    faMethod=None,
    faPercentage=None,
    openClose=None,
    origin=None,
    shortSaleSlot=None,
    designatedLocation=None,
    exemptCode=None,
    discretionaryAmt=None,
    optOutSmartRouting=False,
    auctionStrategy=None,
    startingPrice=None,
    stockRefPrice=None,
    delta=None,
    stockRangeLower=None,
    stockRangeUpper=None,
    volatility=None,
    volatilityType=None,
    continuousUpdate=None,
    referencePriceType=None,
    deltaNeutralOrderType=None,
    deltaNeutralSettlingFirm=None,
    deltaNeutralShortSale=None,
    deltaNeutralShortSaleSlot=None,
    deltaNeutralAuxPrice=None,
    deltaNeutralConId=None,
    deltaNeutralClearingAccount=None,
    # deltaNeutralClearingIntent=None,
    deltaNeutralOpenClose=None,
    # deltaNeutralShortSale=None,
    deltaNeutralDesignatedLocation=None,
    basisPoints=None,
    basisPointsType=None,
    scaleInitLevelSize=None,
    scaleSubsLevelSize=None,
    scalePriceIncrement=None,
    scalePriceAdjustValue=None,
    scalePriceAdjustInterval=None,
    scaleProfitOffset=None,
    scaleAutoReset=None,
    scaleInitPosition=None,
    scaleInitFillQty=None,
    scaleRandomPercent=None,
    hedgeType=None,
    hedgeParam=None,
    account=None,
    settlingFirm=None,
    clearingAccount=None,
    clearingIntent=None,
    # Not needed, added in the `FillAdaptiveParams` call,
    algoStrategy=None,
    #  order.algoParams = [],
    whatIf=False,
    algoId="",
    notHeld=None,
    # smartComboRoutingParams = None,
    # orderComboLegs = None,
    # orderMiscOptions = None,
    activeStartTime=None,
    activeStopTime=None,
    scaleTable=None,
    modelCode=None,
    extOperator=None,
    cashQty=None,
    mifid2DecisionMaker=None,
    mifid2DecisionAlgo=None,
    mifid2ExecutionTrader=None,
    mifid2ExecutionAlgo=None,
    dontUseAutoPriceForHedge=None,
    autoCancelDate=None,
    filledQuantity=None,
    refFuturesConId=None,
    autoCancelParent=None,
    shareholder=None,
    imbalanceOnly=None,
    routeMarketableToBbo=None,
    parentPermId=None,
    # advancedErrorOverride=None,
    # manualOrderTime=None,
    # minTradeQty=None,
    # minCompeteSize=None,
    # competeAgainstBestOffset=None,
    # midOffsetAtWhole=None,
    # midOffsetAtHalf=None,
    randomizeSize=None,
    randomizePrice=None,
    referenceContractId=conId,
    isPeggedChangeAmountDecrease=None,
    peggedChangeAmount=None,
    referenceChangeAmount=None,
    # referenceExchangeId=None,
    adjustedOrderType=None,
    triggerPrice=None,
    lmtPriceOffset=None,
    adjustedStopPrice=None,
    # adjustedStopLimitPrice=None,
    # adjustedTrailingAmount=None,
    # adjustableTrailingUnit=None,
    # conditions=None,
    conditionsIgnoreRth=None,
    conditionsCancelOrder=None,
    # softDollarTier=None,
    isOmsContainer=None,
    # discretionaryUpToLimitPrice=None,
    usePriceMgmtAlgo=None,
    # duration=None,
    # postToAts=None
    order_status=OrderStatusRecord2(
      rid=str(uuid4()),
      at=millis_epoch(nowT),
      order_id=orderId if orderId else 0,
      status=IbOrderStatus.NEW,
      filled=0.0,
      remaining=float(trade),
      avg_fill_price=0.0,
      perm_id=0,
      last_fill_price=0.0,
      client_id=0,
      why_held="",
      mkt_cap_price=0.0
    )
  )
  return order


class OrderRecordOps(RepoOps[OrderRecord2]):
  def __init__(self) -> None:
    super().__init__(OrderRecord2)

  def findByPermId(self, permId: int) -> Callable[[UnitOfWork], Optional[OrderRecord2]]:
    return self.find_one(
      lambda q: q.where(OrderRecord2.permId == permId)
    )
