import logging
import datetime

from ibapi import wrapper
from ibapi.client import EClient
from ibapi.common import TickerId
from ibapi.utils import current_fn_name

from salduba.ib_tws_proxy.operations import ErrorResponse, OperationsTracker

_logger = logging.getLogger(__name__)


class Listener(wrapper.EWrapper):
  ignoreErrors = [2104, 2106, 2158]

  def __init__(self, tracker: OperationsTracker) -> None:
    wrapper.EWrapper.__init__(self)
    self.responseTracker = tracker
    self.done = False

  def error(self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
    if errorCode in Listener.ignoreErrors:
      pass
    elif (errorCode == 504):
      # Not connected, so stop
      self.stop("Got a 'Not Connected' error")
    else:
      self.responseTracker.error(ErrorResponse(reqId, errorCode, errorString, advancedOrderRejectJson))
      super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
      if self.responseTracker.isIdle():
        self.stop("Tracker is Idle")

  def isActive(self) -> bool:
    return not self.done and self.responseTracker.started

  def stop(self, reason: str = ""):
    msg = f"Stopping at {datetime.datetime.now()} because of {reason}" if str else f"Stopping at {datetime.datetime.now()}"
    _logger.info(msg)
    self.responseTracker.dump(_logger.debug)
    self.done = True

  # if hasattr(self, 'account'):
  #   self.start()

  # if advancedOrderRejectJson:
  #     print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString, "AdvancedOrderRejectJson:", advancedOrderRejectJson)
  # else:
  #     print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)


class Stub(EClient):
  def _init__(self, wrapper: Listener) -> None:
    EClient.__init__(self, wrapper=wrapper)  # type: ignore


class ProxyBase(Stub, Listener):
  def __init__(self, logLevel: int = logging.INFO) -> None:
    self.accounts: list[str] = []
    self.tracker = OperationsTracker()
    Listener.__init__(self, self.tracker)
    Stub.__init__(self, wrapper=self)
    _logger.setLevel(logLevel)

  def sendMsg(self, msg: str) -> None:
    caller = current_fn_name(1)
    if caller != 'startApi':
      self.tracker.request(caller, msg)
    super().sendMsg(msg)  # type: ignore
    
  # Need to receive both a nextValidId and a managedAccounts to start
  def nextValidId(self, orderId: int) -> None:
    _logger.debug("Updating the nextValidId to: %s", orderId)
    self.tracker.syncOpId(orderId)
    self.startIfPossible()

  def managedAccounts(self, accountsList: str) -> None:
    _logger.info(f"Receiving Accounts: {accountsList}")
    self.accounts = accountsList.split(',')
    self.startIfPossible()

  def startIfPossible(self) -> None:
    _logger.debug("Start() called")
    if (not self.tracker.isStarted() and self.tracker.isInitialized() and self.accounts):
      self.tracker.start()
#      threading.Thread(target=self.doIt).start()
      self.doIt()

  # Concrete Proxies need to implement this.
  def doIt(self) -> None:
    raise Exception("The Method doIt() must be implemented")

  # Proxy Management

  def stop(self, reason: str = ""):
    super().stop(reason)
    self.disconnect()
