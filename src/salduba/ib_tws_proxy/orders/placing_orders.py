import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Optional, Union

from ibapi.common import OrderId  # pyright: ignore
from ibapi.contract import Contract  # pyright: ignore
from ibapi.order import Order  # pyright: ignore
from ibapi.order_state import OrderState  # pyright: ignore

from salduba.common.persistence.alchemy.db import Db
from salduba.corvino.persistence.movement_record import MovementRecord2
from salduba.ib_tws_proxy.base_proxy.tws_proxy import BaseProxy
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecordOps
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord2, OrderRecordOps

_logger = logging.getLogger(__name__)


@dataclass
class OrderStatusResponse:
    orderId: int
    status: str
    filled: Decimal
    remaining: Decimal
    avgFillPrice: float
    permId: int
    parentId: int
    lastFillPrice: float
    clientId: int
    whyHeld: str
    mktCapPrice: float


@dataclass
class OpenOrderResponse:
    orderId: int
    contract: Contract
    order: Order


OrderResponse = Union[OpenOrderResponse, OrderStatusResponse]


PlaceOrderPostProcessor = Callable[[int, Contract, OrderRecord2, OrderState], OrderResponse]

"""markdown
See:
- [placeOrder](https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html#aa6ff6f6455c551bef9d66c34d1c8586c)
- [openOrder callback](https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#aa05258f1d005accd3efc0d60bc151407)
- [orderStatus callback](https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#a27ec36f07dff982f50968c8a8887d676)
"""  # noqa: E501


@dataclass
class OrderNotification:
  orderId: OrderId
  contract: Contract
  order: Order
  orderState: OrderState


class PlaceOrders(BaseProxy):
  def __init__(
      self,
      db: Db,
      targets: list[MovementRecord2],
      orderRepo: OrderRecordOps,
      contractRepo: ContractRecordOps,
      postProcess: PlaceOrderPostProcessor,
      host: str,
      port: int,
      clientId: int,
      timeout: float = 15 * 60,
      delay: Optional[float] = None,
  ) -> None:
      super().__init__(host, port, clientId, timeout=timeout)
      self.db = db
      self.orderRepo = orderRepo
      self.contractRepo = contractRepo
      self.targets: list[MovementRecord2] = targets
      self.postProcess = postProcess
      self.delay = delay
      self.newlyOrdered: dict[int, MovementRecord2] = {}
      self.previousOrderMessages: dict[int, list[OrderNotification]] = {}

  def runCommands(self) -> None:
    if not self.targets or len(self.targets) == 0:
      _logger.error("No targets to place")
      self.stop("No Orders to Place")
    else:
      _logger.debug(f"Will place {len(self.targets)} orders")
      for movement in self.targets:
        with self._lock:
          oid: Optional[int] = self.responseTracker.nextOpId()
          if oid:
            if not movement.order.orderId:
              movement.order.orderId = oid
            _logger.info(
              f"Placing order[{oid} of type {movement.order.orderType} for {movement.contract.symbol}]"
              f"with strategy: {movement.order.algoStrategy}"
            )
            _logger.debug(f"Placing Order: {movement.order.__dict__}")
            order: Order = movement.order.toOrder()
            contract: Contract = movement.contract.to_contract()
            self.placeOrder(oid, contract, order)
            self.newlyOrdered[oid] = movement
          else:
            _logger.error("Cannot Generate Order Id")
        if self.delay:
          time.sleep(self.delay)
      _logger.debug("Placed Orders, requesting Updates")
      self.reqOpenOrders()

  def orderStatus(
      self,
      orderId: OrderId,
      status: str,
      filled: float,
      remaining: float,
      avgFillPrice: float,
      permId: int,
      parentId: int,
      lastFillPrice: float,
      clientId: int,
      whyHeld: str,
      mktCapPrice: float,
  ) -> None:
      _logger.info(
          f"""
    Receiving: orderStatus[{orderId}]
    status: {status}
    filled: {filled}
    remaining: {remaining}
    avgFillPrice: {avgFillPrice}
    permId: {permId}
    parentId: {parentId}
    lastFillPrice: {lastFillPrice}
    clientId: {clientId}
    whyHeld: {whyHeld}
    mktCapPrice: {mktCapPrice}
  """
      )

  def openOrder(
      self,
      orderId: OrderId,
      contract: Contract,
      order: Order,
      orderState: OrderState,
  ) -> None:
      _logger.info(f"Receiving: openOrder[{orderId}] for {contract.symbol}")
      with self._lock:
          pendingMovement = self.newlyOrdered.get(orderId)
      if not pendingMovement:
          msg = f"Received openOrder for not pending orderId: {orderId}"
          _logger.info(msg)
          if orderId not in self.previousOrderMessages:
            self.previousOrderMessages[orderId] = []
          self.previousOrderMessages[orderId].append(OrderNotification(orderId, contract, order, orderState))
      else:
          # del self.pendingOrders[orderId]
          self.partialResponse(orderId, {"openOrder": (contract, order, orderState)})
          self.completeResponse(orderId)
          self.postProcess(orderId, contract, pendingMovement.order, orderState)

  def openOrderEnd(self) -> None:
      _logger.warning("Received openOrderEnd")
      self.stop("Received OpenOrderEnd")
