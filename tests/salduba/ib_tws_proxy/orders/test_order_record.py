from datetime import datetime
from typing import Set, Tuple

from ibapi.order import Order  # pyright: ignore
from sqlalchemy import inspect

from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord2, newOrderRecord

probe = {
  # "eTradeOnly": False,
  # "firmQuoteOnly": False,
  "rid": "RID",
  'at': 1111,
  'orderId': 22222,
  'clientId': 121212,
  'action': 'BUY',
  'orderType': 'MKT',
  'transmit': False,
  'permId': 55555,
  'solicited': False,
  'totalQuantity': 100.11,
  'lmtPrice': 200.22,
  'auxPrice': 300.33,
  'tif': 'tif',
  'ocaGroup': 'ocaGroup',
  'ocaType': 22,
  'orderRef': 'orderRef',
  'parentId': 'parentId',
  'blockOrder': False,
  'sweepToFill': False,
  'displaySize': 33,
  'triggerMethod': 1928374655,
  'outsideRth': True,
  'hidden': True,
  'goodAfterTime': "goodAfterTime",
  'goodTillDate': "goodTillDate",
  'overridePercentageConstraints': True,
  'rule80A': "rule80A",
  'allOrNone': True,
  'minQty': 1928374655,
  'percentOffset': 12345.4321,
  'trailStopPrice': 12345.4321,
  'trailingPercent': 12345.4321,
  'faGroup': "faGroup",
  'faMethod': "faMethod",
  'faPercentage': "faPercentage",
  'openClose': "openClose",
  'origin': 1928374655,
  'shortSaleSlot': 1928374655,
  'designatedLocation': "designatedLocation",
  'exemptCode': 1928374655,
  'discretionaryAmt': 12345.4321,
  'optOutSmartRouting': True,
  'auctionStrategy': 1928374655,
  'startingPrice': 12345.4321,
  'stockRefPrice': 12345.4321,
  'delta': 12345.4321,
  'stockRangeLower': 12345.4321,
  'stockRangeUpper': 12345.4321,
  'volatility': 12345.4321,
  'volatilityType': 1928374655,
  'continuousUpdate': 1928374655,
  'referencePriceType': 1928374655,
  'deltaNeutralOrderType': "deltaNeutralOrderType",
  'deltaNeutralAuxPrice': 12345.4321,
  'deltaNeutralConId': 1928374655,
  'deltaNeutralSettlingFirm': "deltaNeutralSettlingFirm",
  'deltaNeutralClearingAccount': "deltaNeutralClearingAccount",
  'deltaNeutralOpenClose': "deltaNeutralOpenClose",
  'deltaNeutralShortSale': "deltaNeutralShortSale",
  'deltaNeutralShortSaleSlot': "deltaNeutralShortSaleSlot",
  'deltaNeutralDesignatedLocation': "deltaNeutralDesignatedLocation",
  'basisPoints': 12345.4321,
  'basisPointsType': 1928374655,
  'scaleInitLevelSize': 1928374655,
  'scaleSubsLevelSize': 1928374655,
  'scalePriceIncrement': 12345.4321,
  'scalePriceAdjustValue': 12345.4321,
  'scalePriceAdjustInterval': 1928374655,
  'scaleProfitOffset': 12345.4321,
  'scaleAutoReset': True,
  'scaleInitPosition': 1928374655,
  'scaleInitFillQty': 1928374655,
  'scaleRandomPercent': True,
  'hedgeType': "hedgeType",
  'hedgeParam': "hedgeParam",
  'account': "account",
  'settlingFirm': "settlingFirm",
  'clearingAccount': "clearingAccount",
  'clearingIntent': "clearingIntent",
  'algoStrategy': "algoStrategy",
  'whatIf': True,
  'algoId': "algoId",
  'notHeld': True,
  'activeStartTime': "activeStartTime",
  'activeStopTime': "activeStopTime",
  'scaleTable': "scaleTable",
  'modelCode': "modelCode",
  'extOperator': "extOperator",
  'cashQty': 12345.4321,
  'mifid2DecisionMaker': "mifid2DecisionMaker",
  'mifid2DecisionAlgo': "mifid2DecisionAlgo",
  'mifid2ExecutionTrader': "mifid2ExecutionTrader",
  'mifid2ExecutionAlgo': "mifid2ExecutionAlgo",
  'dontUseAutoPriceForHedge': True,
  'autoCancelDate': "autoCancelDate",
  'filledQuantity': 12345.4321,
  'refFuturesConId': 1928374655,
  'autoCancelParent': True,
  'shareholder': "shareholder",
  'imbalanceOnly': True,
  'routeMarketableToBbo': True,
  'parentPermId': 1928374655,
  'randomizeSize': True,
  'randomizePrice': True,
  'referenceContractId': 1928374655,
  'isPeggedChangeAmountDecrease': True,
  'peggedChangeAmount': 12345.4321,
  'referenceChangeAmount': 12345.4321,
  'adjustedOrderType': "adjustedOrderType",
  'triggerPrice': 12345.4321,
  'lmtPriceOffset': 12345.4321,
  'adjustedStopPrice': 12345.4321,
  'conditionsIgnoreRth': True,
  'conditionsCancelOrder': True,
  'isOmsContainer': True,
  'usePriceMgmtAlgo': True,
}


def test_order_record() -> None:
  underTest = OrderRecord2(**probe)
  rs = {k: v for k, v in underTest.__dict__.items() if not k.startswith('_')}
  assert rs == probe, "The fields should all match"


def test_to_order() -> None:
  orderRecord, order = record_to_order()
  from_order = {}
  from_record = {}
  check_keys = (c.key for c in inspect(OrderRecord2).columns
                if (c.key not in ['rid', 'at'])
                and not c.key.startswith('_')
                and not c.key.endswith('_fk')
                and not c.key == 'algoStrategy')
  print(f"##### Check Keys: {check_keys}")
  for f in check_keys:
    from_order[f] = getattr(order, f)
    from_record[f] = orderRecord.__dict__[f]
  assert from_order == from_record


def record_to_order() -> Tuple[OrderRecord2, Order]:
  underTest: OrderRecord2 = OrderRecord2(**probe)
  order = underTest.toOrder()
  return underTest, order


def test_fields_present() -> None:
  target = newOrderRecord(22, 222, datetime.now(), "orderRef", False, 33333)
  missing: list[str] = []
  keys = target.__dict__.keys()
  for k in (c.key for c in inspect(OrderRecord2).columns
            if not c.key.startswith('_')
            and not c.key.endswith('_fk')):
    if k not in keys:
      missing.append(k)

  assert not missing


def test_order_all_fields() -> None:
  target = Order()
  order_fields: Set[str] = set(k for k in target.__dict__.keys())
  missing_keys = set(f.key for f in inspect(OrderRecord2).columns
                     if f.key not in ['rid', 'at']
                     and not f.key.startswith('_')
                     and not f.key.endswith('_fk')
                     and f.key not in order_fields)
  # missing_keys = [f.key for f in inspect(OrderRecord2).columns if f.key not in order_fields]
  assert not missing_keys, f"Not Found: {missing_keys}"


def test_from_order() -> None:
  _, order = record_to_order()
  recovered: OrderRecord2 = OrderRecord2.newFromOrder(str(probe['rid']), int(str(probe['at'])), order)
  assert recovered.rid == probe['rid']
  assert recovered.at == probe['at']
  from_order = {}
  from_probe = {}
  for f in (c.key for c in inspect(OrderRecord2).columns
            if c.key not in ['rid', 'at']
            and not c.key.startswith('_')
            and not c.key.endswith('_fk')):
    from_order[f] = getattr(order, f)
    from_probe[f] = getattr(recovered, f)
  assert from_order == from_probe
