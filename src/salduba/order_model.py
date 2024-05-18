import textwrap
from datetime import datetime
from typing import Any

from ibapi.order import Order


class OrderLabels(object):
    def __init__(self) -> None:
        self.ticker = "Ticker"
        self.id = "Id"
        self.trade = "Trade"


order_labels = OrderLabels()


class LocalOrder(object):
    mappings: dict[str, str] = {
        order_labels.ticker: "str",
        order_labels.id: "int",
        order_labels.trade: "int",
    }
    order_type: str = "MKT"
    referrer: str = f"CorvinoFundManagement{str(datetime.now())}"

    def __init__(
        self,
        acc_id: str,
        id: int,
        ticker: str,
        q: int,
        outside_trading_hours: bool = False,
        time_in_force: str = "DAY",
    ):
        self.acc_id = acc_id
        self.id = id
        self.ticker = ticker
        self.q = q
        self.outside_trading_hours = outside_trading_hours
        self.time_in_force = time_in_force

    def __repr__(self) -> str:
        return textwrap.dedent(
            f"""\
              Order[{self.id}]
                ticker: {self.ticker}
                trade: {self.q}
            """
        )

    def __str__(self) -> str:
        return f"""Order
                ticker: {self.ticker}
                trade: {self.q}
            """

    def side(self) -> str:
        return "BUY" if self.q > 0 else "SELL"

    def to_dict(self, batchId: str, conid: int, exchange: str) -> dict[str, Any]:
        """
        See: https://ibkrcampus.com/ibkr-api-page/cpapi/#place-order for description of fields
        """
        return {
            "acctId": self.acc_id,
            "conid": conid,
            # "conidex": "265598@SMART", Not needed if conid & listing Exchange are provided
            "secType": f"{conid}@{exchange}",
            "cOID": f"{batchId}-{self.id}",
            "parentId": None,
            "orderType": Order.order_type,
            "listingExchange": exchange,
            "isSingleGroup": False,
            "outsideRTH": self.outside_trading_hours,
            # "price": 185.50, Not required for direct orders
            # "auxPrice": 183, Not required for direct orders
            "side": self.side(),
            "ticker": self.ticker,
            "tif": self.time_in_force,
            # "trailingAmt": 1.00, Not required for direct orders
            # "trailingType": "amt", Not required for direct orders
            "referrer": Order.referrer,
            "quantity": abs(self.q),
            # Can not be used in tandem with quantity value.
            # "cashQty": {{ cashQty }},
            # "fxQty": {{ fxQty }},
            "useAdaptive": False,  # Don't use Price Management Algorithm
            "isCcyConv": False,  # Not a FX conversion order
            # May specify an allocation method such as Equal or NetLiq for Financial Advisors.
            # "allocationMethod": {{ allocationMethod }},
            # "allocationMethod" = "???",  # Not required
            # manualOrderTime = 12345,  # not required, only for Brokers & Advisors
            "deactivated": True,  # Save the order, don't execute
            # "strategy": "Vwap",  # Not required, check default?
            # "strategyParameters": {  # Not Required
            #    "MaxPctVol":"0.1",
            #  "StartTime":"14:00:00 EST",
            #  "EndTime":"15:00:00 EST",
            #  "AllowPastEndTime":true
            # }
        }
