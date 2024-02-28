from typing import Optional
from enum import StrEnum
from _decimal import Decimal
import logging
import time
import datetime

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.contract import ContractDescription
from ibapi.order import Order
from ibapi.common import ListOfContractDescription
from ibapi.common import TickerId
from ibapi.utils import (
    current_fn_name
)

from samples.AvailableAlgoParams import AvailableAlgoParams



class Exchange(StrEnum):
  NASDAQ = 'NASDAQ'
  SMART = 'SMART'


class SecType(StrEnum):
  STK = 'STK'
  CASH = 'CASH'
  FUT = 'FUT'


class OrderTif(StrEnum):
  DAY = 'DAY'
  GTC = 'GTC'
  IOC = 'IOC'
  GTD = 'GTD'
  OPG = 'OPG'
  FOK = 'FOK'
  DTC = 'DTC'


class Action(StrEnum):
  BUY = 'BUY'
  SELL = 'SELL'


class OrderType(StrEnum):
  LMT = 'LMT'
  LIT = 'LIT'
  MKT = 'MKT'



class PlaceOrders(ProxyBase):
  def __init__(self, movements: dict[str, Movement], selection: list[str] = [], searchDelay: int = 1) -> None:
    ProxyBase.__init__(self)
    self.movements: dict[str, Movement] = movements \
      if (len(selection) == 0) else {k : v for (k, v) in movements.items() if k.upper() in selection}
    self.searchDelay = searchDelay
  # Requests

  def findContractDetails(self, name: str) -> Optional[RequestResult]:
    oid: int = self.tracker.nextOpId()
    self.reqMatchingSymbols(oid, name)

  def doIt(self) -> None:
    logging.info(f"Sending {len(self.movements)} movements")
    for m in self.movements.values():
      self.findContractDetails(m.name)
      time.sleep(self.searchDelay)

  # Callback
  def symbolSamples(self, reqId: int,
                    contractDescriptions: ListOfContractDescription) -> None:   # type: ignore
    self.tracker.complete(SuccessResponse(reqId))
    descriptions: list[ContractDescription] = contractDescriptions
    for cd in descriptions:
      d: Contract = cd.contract
      if not d.exchange:
        d.exchange = d.primaryExchange
      d_dict = {
        'conId': d.conId,
        'symbol': d.symbol,
        'secType': d.secType,
        'lastTradeDateOrContractMonth': d.lastTradeDateOrContractMonth,
        'strike': d.strike,
        'right': d.right,
        'multiplier': d.multiplier,
        'exchange': d.exchange,
        'primaryExchange': d.primaryExchange,
        'currency': d.currency,
        'localSymbol': d.localSymbol,
        'tradingClass': d.tradingClass,
        'includeExpired': d.includeExpired,
        'secIdType': d.secIdType,
        'secId': d.secId,
        'description': d.description,
        'issuerId': d.issuerId
      }
      logging.info(f"symbol ANSWER: {d_dict}")
    if not descriptions:
      logging.error("No Contracts returned")
    else:
      if len(descriptions) > 1:
        logging.error(f"Multiple Contracts returned: {descriptions}")
      else:
        contract: Contract = descriptions[0].contract
        movement: Optional[Movement] = self.movements.get(contract.description)
        if not movement:
          logging.error(f"No Movement found for: {contract}")
        else:
          if movement.overrideExchange:
            contract.exchange = movement.overrideExchange
          movement.contract = contract
          order = self.orderForMovement(movement)
          if order:
            movement.order = order
          else:
            logging.warn(f"Order not found for movement: {movement.name}")
          self.placeMovement(movement, "SMART")
    if self.tracker.isIdle():
      self.stop("Tracker is Idle")

  def placeMovement(self, movement: Movement, overrideExchange: Optional[str] = None) -> None:
    logging.info(f"Trying to place order for {movement.name}")
    if movement.contract is not None and movement.order is not None:
      if overrideExchange:
        movement.contract.exchange = overrideExchange
      elif movement.overrideExchange:
        movement.contract.exchange = movement.overrideExchange
      logging.info(f"With Movement: {movement}")
      self.placeOrder(self.tracker.nextOpId(), movement.contract, movement.order)   # type: ignore
    else:
      logging.warn(f"Cannot Place Movement {movement.name}, missing contract or order")

  def orderStatus(self,
                  orderId: int,
                  status: str,
                  filled: Decimal,
                  remaining: Decimal,
                  avgFillPrice: float,
                  permId: int,
                  parentId: int,
                  lastFillPrice: float,
                  clientId: int,
                  whyHeld: str,
                  mktCapPrice: float) -> None:
    self.tracker.response(SuccessResponse(orderId, f"Received: {current_fn_name(0)}"))
    logging.info(f"Got an OrderStatus for reqId: {orderId} with status {status}")

  # Auxiliary
  def orderForMovement(self, movement: Movement) -> Optional[Order]:
    """
    See: https://docs.google.com/spreadsheets/d/1pmFZ79c6chsPgXl_YJel3_k_0iu04KiPCioYGRCZFyo/edit#gid=0

    For interpretation of fields and values to assign.
    """
    if movement.contract:
      order: Order = Order()
      order.orderId = movement.orderId
      order.solicited = False
      order.action = Action.BUY if movement.trade > 0 else Action.SELL
      order.totalQuantity = Decimal(abs(movement.trade))
      order.orderType = OrderType.MKT
      # order.lmtPrice: float = 0.0
      order.tif = OrderTif.DAY
      # order.ocaGroup = ""
      # order.ocaType: int = 0
      order.orderRef = movement.orderRef
      order.transmit = False
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
    else:
      logging.error("Cannot place order for movement without Contract: {movement.name}")
      return None
