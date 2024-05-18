import logging
from decimal import Decimal
from typing import Any, Optional, Self

from ibapi.common import OrderId
from ibapi.order import Order

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.model import db_version
from salduba.ib_tws_proxy.backing_db.record import Record, RecordMeta
from salduba.ib_tws_proxy.backing_db.repo import Repo, SortDirection
from salduba.ib_tws_proxy.domain.enumerations import IbOrderStatus

_logger = logging.getLogger(__name__)


# https://interactivebrokers.github.io/tws-api/classIBApi_1_1Order.html
orderCompanion = RecordMeta(
    "ORDER_T",
    [
        "orderId",  # int
        "solicited",  # bool
        "clientId",  # int
        "permId",  # int
        "action",  # EnumStr (BUY/SELL)
        "totalQuantity",  # decimal
        "orderType",  # str
        "lmtPrice",  # double
        "auxPrice",  # double
        "tif",  # StrEnum
        "ocaGroup",  # str
        "ocaType",  # IntEnum
        "orderRef",  # str
        "transmit",  # bool
        "parentId",  # int
        "blockOrder",  # bool
        "sweepToFill",  # bool
        "displaySize",  # int
        "triggerMethod",  # IntEnum
        "outsideRth",  # bool
        "hidden",  # bool
        "goodAfterTime",  # str (date)
        "goodTillDate",  # str (date)
        "overridePercentageConstraints",  # bool
        "rule80A",  # StrEnum
        "allOrNone",  # bool
        "minQty",  # int
        "percentOffset",  # double
        "trailStopPrice",  # double
        "trailingPercent",  # double
        "faGroup",  # str
        "faMethod",  # str
        "faPercentage",  # str
        "openClose",  # str
        "origin",  # IntEnum
        "shortSaleSlot",  # IntEnum
        "designatedLocation",  # str
        "exemptCode",  # int
        "discretionaryAmt",  # double
        "optOutSmartRouting",  # bool
        "auctionStrategy",  # IntEnum
        "startingPrice",  # double
        "stockRefPrice",  # double
        "delta",  # double
        "stockRangeLower",  # double
        "stockRangeUpper",  # double
        "volatility",  # double
        "volatilityType",  # IntEnum
        "continuousUpdate",  # int
        "referencePriceType",  # IntEnum
        "deltaNeutralOrderType",  # str (??)
        "deltaNeutralAuxPrice",  # double
        "deltaNeutralConId",  # int
        "deltaNeutralSettlingFirm",  # str
        "deltaNeutralClearingAccount",  # str
        "deltaNeutralOpenClose",  # str
        "deltaNeutralShortSale",  # bool
        "deltaNeutralShortSaleSlot",  # int
        "deltaNeutralDesignatedLocation",  # str
        "basisPoints",  # double
        "basisPointsType",  # int
        "scaleInitLevelSize",  # int
        "scaleSubsLevelSize",  # int
        "scalePriceIncrement",  # double
        "scalePriceAdjustValue",  # double
        "scalePriceAdjustInterval",  # int
        "scaleProfitOffset",  # double
        "scaleAutoReset",  # bool
        "scaleInitPosition",  # int
        "scaleInitFillQty",  # int
        "scaleRandomPercent",  # bool
        "hedgeType",  # StrEnum
        "hedgeParam",  # str
        "account",  # str
        "settlingFirm",  # str
        "clearingAccount",  # str
        "clearingIntent",  # StrEnum
        "algoStrategy",  # StrEnum
        # algoParams: List[TagValue]
        "whatIf",  # bool
        "algoId",  # str
        "notHeld",  # bool
        # smartComboRoutingParams: List[TagValue]
        # orderComboLegs: List[OrderComboLeg]
        # orderMiscOptions: List[TagValue]
        "activeStartTime",  # str (date-time)
        "activeStopTime",  # str (date-time)
        "scaleTable",  # str
        "modelCode",  # str
        "extOperator",  # str
        "cashQty",  # double
        "mifid2DecisionMaker",  # str
        "mifid2DecisionAlgo",  # str
        "mifid2ExecutionTrader",  # str
        "mifid2ExecutionAlgo",  # str
        "dontUseAutoPriceForHedge",  # str
        "autoCancelDate",  # str (date)
        "filledQuantity",  # decimal
        "refFuturesConId",  # int
        "autoCancelParent",  # bool
        "shareholder",  # str
        "imbalanceOnly",  # bool
        "routeMarketableToBbo",  # bool
        "parentPermId",  # long
        "advancedErrorOverride",  # str
        "manualOrderTime",  # str (date-time)
        "minTradeQty",  # int
        "minCompeteSize",  # int
        "competeAgainstBestOffset",  # double
        "midOffsetAtWhole",  # double
        "midOffsetAtHalf",  # double
        "randomizeSize",  # bool
        "randomizePrice",  # bool
        "referenceContractId",  # int
        "isPeggedChangeAmountDecrease",  # bool
        "peggedChangeAmount",  # double
        "referenceChangeAmount",  # double
        "adjustedOrderType",  # str
        "triggerPrice",  # double
        "lmtPriceOffset",  # double
        "adjustedStopPrice",  # double
        "adjustedTrailingAmount",  # double
        # conditions: List[OrderConditions]
        "conditionsIgnoreRth",  # bool
        "conditionsCancelOrder",  # bool
        # tier: SoftDollarTier
        "isOmsContainer",  # bool
        "discretionaryUpToLimitPrice",  # bool
        "usePriceMgmtAlgo",  # bool
        "duration",  # int
        "postToAts",  # int
    ],
    db_version,
)


class OrderRecord(Record):
    def __init__(self, rid: str, at: int, *argsv: list[Any]) -> None:
        super().__init__(rid, at, orderCompanion, *argsv)

    def toOrder(self) -> Order:
        result = Order()
        rd = result.__dict__
        for k in orderCompanion.own_fields:
            rd[k] = self.__dict__[k]
        return result

    @classmethod
    def fromOrder2(cls, rid: str, at: int, order: Order) -> Self:
        return cls.from_dict(rid, at, orderCompanion, order.__dict__)

    @classmethod
    def fromOrder(cls, rid: str, at: int, order: Order) -> Self:
        return cls.hydrate(
            rid,
            at,
            order.orderId,
            order.solicited,
            order.clientId,
            order.permId,
            order.action,
            order.totalQuantity,
            order.orderType,
            order.lmtPrice,
            order.auxPrice,
            order.tif,
            order.ocaGroup,
            order.ocaType,
            order.orderRef,
            order.transmit,
            order.parentId,
            order.blockOrder,
            order.sweepToFill,
            order.displaySize,
            order.triggerMethod,
            order.outsideRth,
            order.hidden,
            order.goodAfterTime,
            order.goodTillDate,
            order.overridePercentageConstraints,
            order.rule80A,
            order.allOrNone,
            order.minQty,
            order.percentOffset,
            order.trailStopPrice,
            order.trailingPercent,
            order.faGroup,
            order.faMethod,
            order.faPercentage,
            order.openClose,
            order.origin,
            order.shortSaleSlot,
            order.designatedLocation,
            order.exemptCode,
            order.discretionaryAmt,
            order.optOutSmartRouting,
            order.auctionStrategy,
            order.startingPrice,
            order.stockRefPrice,
            order.delta,
            order.stockRangeLower,
            order.stockRangeUpper,
            order.volatility,
            order.volatilityType,
            order.continuousUpdate,
            order.referencePriceType,
            order.deltaNeutralOrderType,
            order.deltaNeutralAuxPrice,
            order.deltaNeutralConId,
            order.deltaNeutralSettlingFirm,
            order.deltaNeutralClearingAccount,
            order.deltaNeutralOpenClose,
            order.deltaNeutralShortSale,
            order.deltaNeutralShortSaleSlot,
            order.deltaNeutralDesignatedLocation,
            order.basisPoints,
            order.basisPointsType,
            order.scaleInitLevelSize,
            order.scaleSubsLevelSize,
            order.scalePriceIncrement,
            order.scalePriceAdjustValue,
            order.scalePriceAdjustInterval,
            order.scaleProfitOffset,
            order.scaleAutoReset,
            order.scaleInitPosition,
            order.scaleInitFillQty,
            order.scaleRandomPercent,
            order.hedgeType,
            order.hedgeParam,
            order.account,
            order.settlingFirm,
            order.clearingAccount,
            order.clearingIntent,
            order.algoStrategy,
            order.whatIf,
            order.algoId,
            order.notHeld,
            order.activeStartTime,
            order.activeStopTime,
            order.scaleTable,
            order.modelCode,
            order.extOperator,
            order.cashQty,
            order.mifid2DecisionMaker,
            order.mifid2DecisionAlgo,
            order.mifid2ExecutionTrader,
            order.mifid2ExecutionAlgo,
            order.dontUseAutoPriceForHedge,
            order.autoCancelDate,
            order.filledQuantity,
            order.refFuturesConId,
            order.autoCancelParent,
            order.shareholder,
            order.imbalanceOnly,
            order.routeMarketableToBbo,
            order.parentPermId,
            order.advancedErrorOverride,
            order.manualOrderTime,
            order.minTradeQty,
            order.minCompeteSize,
            order.competeAgainstBestOffset,
            order.midOffsetAtWhole,
            order.midOffsetAtHalf,
            order.randomizeSize,
            order.randomizePrice,
            order.referenceContractId,
            order.isPeggedChangeAmountDecrease,
            order.peggedChangeAmount,
            order.referenceChangeAmount,
            order.adjustedOrderType,
            order.triggerPrice,
            order.lmtPriceOffset,
            order.adjustedStopPrice,
            order.adjustedTrailingAmount,
            order.conditionsIgnoreRth,
            order.conditionsCancelOrder,
            order.isOmsContainer,
            order.discretionaryUpToLimitPrice,
            order.usePriceMgmtAlgo,
            order.duration,
            order.postToAts,
        )


softDollarTierCompanion = RecordMeta(
    "SOFT_DOLLAR_TIER",
    [
        "name",  # str
        "value",  # str
        "displayName",  # str
        "order_fk",  # str ref to Order
    ],
    db_version,
)


class SoftDollarTierRecord(Record):
    def __init__(self, rid: str, at: int, *args: list[Any]) -> None:
        super().__init__(rid, at, softDollarTierCompanion, *args)


class SoftDollarTierRepo(Repo[RecordMeta, SoftDollarTierRecord]):
    def __init__(self, db: TradingDB) -> None:
        super().__init__(db, softDollarTierCompanion, SoftDollarTierRecord.hydrate)


orderStatusCompanion = RecordMeta(
    table="ORDER_STATUS",
    own_fields=[
        "orderId",  # OrderId
        "status",  # IbOrderStatus
        "filled",  # Decimal
        "remaining",  # Decimal
        "avgFillPrice",  # float
        "permId",  # int
        "parentId",  # int
        "lastFillPrice",  # float
        "clientId",  # int
        "whyHeld",  # str
        "mktCapPrice",  # float
        "order_fk",  # str
    ],
    db_version=db_version,
)


class OrderStatusRecord(Record):
    def __init__(
        self,
        rid: str,
        at: int,
        orderId: OrderId,
        status: IbOrderStatus,
        filled: Decimal,
        remaining: Decimal,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float,
        orderFk: str,
    ) -> None:
        super().__init__(
            rid,
            at,
            orderStatusCompanion,
            orderId,
            status,  # type: ignore
            filled,  # type: ignore
            remaining,  # type: ignore
            avgFillPrice,  # type: ignore
            permId,  # type: ignore
            parentId,  # type: ignore
            lastFillPrice,  # type: ignore
            clientId,  # type: ignore
            whyHeld,  # type: ignore
            mktCapPrice,  # type: ignore
            orderFk,  # type: ignore
        )


class OrderStatusRepo(Repo[RecordMeta, OrderStatusRecord]):
    orderFKClause = "(order_fk = ?)"

    def __init__(self, db: TradingDB) -> None:
        super().__init__(db, orderStatusCompanion, OrderStatusRecord.hydrate)

    def recordsForOrder(self, orderId: str) -> list[OrderStatusRecord]:
        return self.select(
            [orderId],
            [OrderStatusRepo.orderFKClause],
            [("at", SortDirection.DESC)],
        )


class OrderRepo(Repo[RecordMeta, OrderRecord]):
    permIdClause = "(permId = ?)"

    def __init__(
        self,
        db: TradingDB,
        sdTierRepo: SoftDollarTierRepo,
        orderStatusRepo: OrderStatusRepo,
    ) -> None:
        super().__init__(db, orderCompanion, OrderRecord.hydrate)
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
