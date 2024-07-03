import logging
from dataclasses import dataclass
from typing import Optional

from ibapi.common import OrderId
from ibapi.order import Order

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.record import Record
from salduba.ib_tws_proxy.backing_db.repo import Repo, SortDirection
from salduba.ib_tws_proxy.domain.enumerations import IbOrderStatus

_logger = logging.getLogger(__name__)


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
@dataclass
class OrderRecord(Record):
  table = 'ORDER_T'
  orderId: int
  clientId: int
  action: str
  orderType: str
  transmit: bool
  permId: Optional[int] = None
  solicited: Optional[bool] = None
  totalQuantity: Optional[float] = None
  lmtPrice: Optional[float] = None
  auxPrice: Optional[float] = None
  tif: Optional[str] = None
  ocaGroup: Optional[str] = None
  ocaType: Optional[int] = None
  orderRef: Optional[str] = None
  parentId: Optional[int] = None
  blockOrder: Optional[bool] = None
  sweepToFill: Optional[bool] = None
  displaySize: Optional[int] = None
  triggerMethod: Optional[int] = None
  outsideRth: Optional[bool] = None
  hidden: Optional[bool] = None
  goodAfterTime: Optional[str] = None
  goodTillDate: Optional[str] = None
  overridePercentageConstraints: Optional[bool] = None
  rule80A: Optional[str] = None
  allOrNone: Optional[bool] = None
  minQty: Optional[int] = None
  percentOffset: Optional[float] = None
  trailStopPrice: Optional[float] = None
  trailingPercent: Optional[float] = None
  faGroup: Optional[str] = None
  faMethod: Optional[str] = None
  faPercentage: Optional[str] = None
  openClose: Optional[str] = None
  origin: Optional[int] = None
  shortSaleSlot: Optional[int] = None
  designatedLocation: Optional[str] = None
  exemptCode: Optional[int] = None
  discretionaryAmt: Optional[float] = None
  optOutSmartRouting: Optional[bool] = None
  auctionStrategy: Optional[int] = None
  startingPrice: Optional[float] = None
  stockRefPrice: Optional[float] = None
  delta: Optional[float] = None
  stockRangeLower: Optional[float] = None
  stockRangeUpper: Optional[float] = None
  volatility: Optional[float] = None
  volatilityType: Optional[int] = None
  continuousUpdate: Optional[int] = None
  referencePriceType: Optional[int] = None
  deltaNeutralOrderType: Optional[str] = None
  deltaNeutralAuxPrice: Optional[float] = None
  deltaNeutralConId: Optional[int] = None
  deltaNeutralSettlingFirm: Optional[str] = None
  deltaNeutralClearingAccount: Optional[str] = None
  deltaNeutralOpenClose: Optional[str] = None
  deltaNeutralShortSale: Optional[str] = None
  deltaNeutralShortSaleSlot: Optional[str] = None
  deltaNeutralDesignatedLocation: Optional[str] = None
  basisPoints: Optional[float] = None
  basisPointsType: Optional[int] = None
  scaleInitLevelSize: Optional[int] = None
  scaleSubsLevelSize: Optional[int] = None
  scalePriceIncrement: Optional[float] = None
  scalePriceAdjustValue: Optional[float] = None
  scalePriceAdjustInterval: Optional[int] = None
  scaleProfitOffset: Optional[float] = None
  scaleAutoReset: Optional[bool] = None
  scaleInitPosition: Optional[int] = None
  scaleInitFillQty: Optional[int] = None
  scaleRandomPercent: Optional[bool] = None
  hedgeType: Optional[str] = None
  hedgeParam: Optional[str] = None
  account: Optional[str] = None
  settlingFirm: Optional[str] = None
  clearingAccount: Optional[str] = None
  clearingIntent: Optional[str] = None
  algoStrategy: Optional[str] = None
  whatIf: Optional[bool] = None
  algoId: Optional[str] = None
  notHeld: Optional[bool] = None
  activeStartTime: Optional[str] = None
  activeStopTime: Optional[str] = None
  scaleTable: Optional[str] = None
  modelCode: Optional[str] = None
  extOperator: Optional[str] = None
  cashQty: Optional[float] = None
  mifid2DecisionMaker: Optional[str] = None
  mifid2DecisionAlgo: Optional[str] = None
  mifid2ExecutionTrader: Optional[str] = None
  mifid2ExecutionAlgo: Optional[str] = None
  dontUseAutoPriceForHedge: Optional[bool] = None
  autoCancelDate: Optional[str] = None
  filledQuantity: Optional[float] = None
  refFuturesConId: Optional[int] = None
  autoCancelParent: Optional[bool] = None
  shareholder: Optional[str] = None
  imbalanceOnly: Optional[bool] = None
  routeMarketableToBbo: Optional[bool] = None
  parentPermId: Optional[int] = None
  randomizeSize: Optional[bool] = None
  randomizePrice: Optional[bool] = None
  referenceContractId: Optional[int] = None
  isPeggedChangeAmountDecrease: Optional[bool] = None
  peggedChangeAmount: Optional[float] = None
  referenceChangeAmount: Optional[float] = None
  adjustedOrderType: Optional[str] = None
  triggerPrice: Optional[float] = None
  lmtPriceOffset: Optional[float] = None
  adjustedStopPrice: Optional[float] = None
  conditionsIgnoreRth: Optional[bool] = None
  conditionsCancelOrder: Optional[bool] = None
  isOmsContainer: Optional[bool] = None
  usePriceMgmtAlgo: Optional[bool] = None

  def toOrder(self) -> Order:
    result = Order()
    rd = result.__dict__
    for k in self.own_fields():
      rd[k] = self.__dict__[k]
    return result

  @classmethod
  def newFromOrder(cls, rid: str, at: int, order: Order) -> 'OrderRecord':
    return cls.from_dict(rid, at, order.__dict__)


@dataclass
class SoftDollarTierRecord(Record):
  name: str
  value: str
  displayName: str
  order_fk: str


class SoftDollarTierRepo(Repo[SoftDollarTierRecord]):
  def __init__(self, db: TradingDB) -> None:
    super().__init__(db, SoftDollarTierRecord, "SOFT_DOLLAR_TIER")


@dataclass
class OrderStatusRecord(Record):
  orderId: OrderId
  status: IbOrderStatus
  filled: float
  remaining: float
  avgFillPrice: float
  permId: int
  parentId: int
  lastFillPrice: float
  clientId: int
  whyHeld: str
  mktCapPrice: float
  orderFk: str


class OrderStatusRepo(Repo[OrderStatusRecord]):
  orderFKClause = "(order_fk = ?)"

  def __init__(self, db: TradingDB) -> None:
    super().__init__(db, OrderStatusRecord, "ORDER_STATUS")

  def recordsForOrder(self, orderId: str) -> list[OrderStatusRecord]:
    return self.select(
      [orderId],
      [OrderStatusRepo.orderFKClause],
      [("at", SortDirection.DESC)],
    )


class OrderRepo(Repo[OrderRecord]):
  permIdClause = "(permId = ?)"

  def __init__(
    self,
    db: TradingDB,
    sdTierRepo: SoftDollarTierRepo,
    orderStatusRepo: OrderStatusRepo,
  ) -> None:
    super().__init__(db, OrderRecord, "ORDER_T")
    self.softDollarTierRepo = sdTierRepo
    self.orderStatusRepo = orderStatusRepo

  def findByPermId(self, permId: int) -> Optional[OrderRecord]:
    rs = self.select([permId], [OrderRepo.permIdClause], [("at", SortDirection.DESC)])
    if len(rs) > 1:
      msg = f"Found {len(rs)} Orders (>1) with the same permId: {permId}"
      _logger.error(msg)
      raise Exception(msg)
    else:
      return rs[0] if rs else None
