import datetime
import logging
import sys
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Optional, TextIO, Tuple, Union
from uuid import uuid4

from ibapi.common import OrderId
from ibapi.contract import Contract
from ibapi.execution import Execution
from ibapi.order import Order
from ibapi.order_state import OrderState

from salduba.ib_tws_proxy.base_proxy.tws_proxy import BaseProxy
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo
from salduba.ib_tws_proxy.domain.enumerations import IbOrderStatus
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecord, OrderRepo, OrderStatusRecord
from salduba.util.time import millis_epoch

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


PlaceOrderPostProcessor = Callable[[int, Contract, OrderRecord, OrderState], OrderResponse]

"""markdown
See:
- [placeOrder](https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html#aa6ff6f6455c551bef9d66c34d1c8586c)
- [openOrder callback](https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#aa05258f1d005accd3efc0d60bc151407)
- [orderStatus callback](https://interactivebrokers.github.io/tws-api/interfaceIBApi_1_1EWrapper.html#a27ec36f07dff982f50968c8a8887d676)
"""  # noqa: E501


class PlaceOrders(BaseProxy):
  def __init__(
      self,
      targets: list[Tuple[Contract, Order]],
      orderRepo: OrderRepo,
      contractRepo: ContractRepo,
      postProcess: PlaceOrderPostProcessor,
      host: str,
      port: int,
      clientId: int,
      timeout: float = 15 * 60,
      delay: Optional[float] = None,
  ) -> None:
      super().__init__(host, port, clientId, timeout=timeout)
      self.orderRepo = orderRepo
      self.contractRepo = contractRepo
      self.targets: list[Tuple[Contract, Order]] = targets
      self.postProcess = postProcess
      self.delay = delay
      self.pendingOrders: dict[int, Tuple[Contract, OrderRecord]] = {}

  def runCommands(self) -> None:
    if not self.targets or len(self.targets) == 0:
      _logger.error("No targets to place")
      self.stop("No Orders to Place")
    else:
      _logger.debug(f"Will place {len(self.targets)} orders")
      nowT = datetime.datetime.now()
      for contract, order in self.targets:
        with self._lock:
          oid: Optional[int] = self.responseTracker.nextOpId()
          if oid:
            if not order.orderId:
              order.orderId = oid
            _logger.info(
              f"Placing order[{oid} of type {order.orderType} for {contract.symbol}]"
              f"with strategy: {order.algoStrategy}"
            )
            _logger.debug(f"Placing Order: {order.__dict__}")
            newRecord = OrderRecord.newFromOrder(str(uuid4()), millis_epoch(nowT), order)
            self.orderRepo.insert([newRecord])
            self.placeOrder(oid, contract, order)
            self.pendingOrders[oid] = (contract, newRecord)
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
      filled: Decimal,
      remaining: Decimal,
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
          pendingOrderRecord = self.pendingOrders.get(orderId)
      if not pendingOrderRecord:
          msg = f"Received openOrder for not pending orderId: {orderId}"
          _logger.error(msg)
          raise Exception(msg)
      else:
          _, pendingOrder = pendingOrderRecord
          del self.pendingOrders[orderId]
          self.partialResponse(orderId, {"openOrder": (contract, order, orderState)})
          self.completeResponse(orderId)
          self.postProcess(orderId, contract, pendingOrder, orderState)

  def openOrderEnd(self) -> None:
      _logger.warning("Received openOrderEnd")
      self.stop("Received OpenOrderEnd")


class OrderMonitor(BaseProxy):
  def __init__(
      self,
      orderRepo: OrderRepo,
      contractRepo: ContractRepo,
      postProcess: Callable[[int, Contract, Order, OrderState], list[OrderResponse]],
      host: str,
      port: int,
      clientId: int,
      tIo: Optional[TextIO] = sys.stdout,
      timeout: float = 15 * 60,
      delay: Optional[float] = None,
  ) -> None:
      super().__init__(host, port, clientId, timeout=timeout)
      self.order_repo = orderRepo
      self.contract_repo = contractRepo
      self.post_process = postProcess
      self.delay = delay
      self.tIo = tIo

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
    orderRecord: Optional[OrderRecord] = self.order_repo.findByPermId(permId)
    if not orderRecord:
      msg = f"Received orderStatus for unknown clientId::orderId: {clientId}::{orderId} || {permId}"
      _logger.warning(msg)
      if self.tIo:
          self.tIo.write(msg)
      # raise Exception(msg) Not an error b/c it could have been placed from the UI or other client directly
    else:
      nowEpoch = millis_epoch()
      if self.tIo:
        self.tIo.write(
            f"""
    orderStatus[{orderId}] for Order [{permId}]:
    \t{status}
    \tfilled: {filled}
    \tremaining: {remaining}
    \tclientId: {clientId}
  """
        )
        orderRecord.status = status  # type: ignore
        orderRecord.at = nowEpoch
        with self.order_repo.db as db:
          with db.cursor():
            self.order_repo.update(orderRecord)
            self.order_repo.orderStatusRepo.insert(
              [
                OrderStatusRecord(
                    str(uuid4()),
                    nowEpoch,
                    orderId,
                    IbOrderStatus(status),
                    filled,
                    remaining,
                    avgFillPrice,
                    permId,
                    parentId,
                    lastFillPrice,
                    clientId,
                    whyHeld,
                    mktCapPrice,
                    orderRecord.rid,
                )
              ]
            )

  def execDetails(self, reqId: int, contract: Contract, execution: Execution) -> None:
    if self.tIo:
        self.tIo.write(
            f"""
      Execution[{reqId}] for Order: [{execution.permId}] for {contract.symbol}:
      \tside: {execution.side}
      \tfilled: {execution.shares}
      \tcumQty: {execution.cumQty}
      \tclientId: {execution.clientId}
    """
          )

  def execDetailsEnd(self, reqId: int) -> None:
    if self.tIo:
        self.tIo.write(
            f"""
      Execution[{reqId}] End
      """)
