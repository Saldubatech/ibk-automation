import datetime
import logging
import threading
from typing import Any, Optional

from ibapi.client import EClient
from ibapi.utils import current_fn_name
from ibapi.wrapper import EWrapper

from salduba.ib_tws_proxy.operations import ErrorResponse, OperationsTracker, SuccessResponse

_logger = logging.getLogger(__name__)


class Listener(EWrapper):  # type: ignore
  ignoreErrors: list[int] = [2104, 2106, 2158]

  def __init__(self, tracker: OperationsTracker) -> None:
    EWrapper.__init__(self)
    self.responseTracker = tracker
    self.done = False

  def error(
    self,
    reqId: int,
    errorCode: int,
    errorString: str,
    advancedOrderRejectJson: str = "",
  ) -> None:
    if errorCode in Listener.ignoreErrors:
      pass
    elif errorCode == 502 or errorCode == 504:
      msg = f"Got a 'Not Connected' error({errorCode}): '{errorString}', with {advancedOrderRejectJson}"
      # Not Connected, stop
      self.stop(msg)
    elif errorCode == 2110:
      msg = "TWS connectivity to server is broken. Stopping..."
      self.stop(msg)
    else:
      _logger.error(f"Unexpected Error[{errorCode}]: {errorString} with AOR Info:\n\t{advancedOrderRejectJson}")
      self.responseTracker.error(ErrorResponse(reqId, errorCode, errorString, advancedOrderRejectJson))
      super().error(reqId, errorCode, errorString)
      if self.responseTracker.isIdle():
        _logger.info(f"Tracker found idle at error response: {reqId}")
        _logger.error(f"\nUnexpected Error({errorCode}): {errorString} with:\n\t{advancedOrderRejectJson}")
        self.stop("Tracker is Idle")

  def isActive(self) -> bool:
    return not self.done and self.responseTracker.started

  def stop(self, reason: str = "") -> None:
    msg = f"Stopping at {datetime.datetime.now()} because {reason}" if reason else f"Stopping at {datetime.datetime.now()}"
    _logger.info(msg)
    self.responseTracker.dump(_logger.debug)
    self.done = True


class ClientStub(EClient):  # type: ignore
  def __init__(self, clientId: int, ib_wrapper: Listener) -> None:
    EClient.__init__(self, wrapper=ib_wrapper)
    self.clientId = clientId


class BaseProxy(ClientStub, Listener):
  """
  @startuml (id=PROXY_LIFECYCLE)
  skinparam ranksep 15

  title
  =PROXY EXECUTION LIFECYCLE
  end title

  |Command|
  fork
    -[hidden]->
    start
    :__init__()>
    |Proxy|
    :CREATED;
    |Command|
    :activate()>
    |Proxy|
    :connect()>
    :run()|
    fork
   |Command|
   :return<
   end
    |Proxy|
    fork again
   :managedAccounts()<
   :store Account/
    fork again
   :nextValidId()<
   :tracker.syncOp()|
    end fork {join}
    :start()|
    fork
   :LISTEN_PENDING;
    repeat
      split
     :responsePart<
     :accumulateResponse/
      split again
     :responseEnd<
     :closePendingCommand/
     :processResponses|
      end split
    repeat while (commands pending)
    fork again
   partition performTasks {
     repeat
    :command>
    :registerPendingCommand/
    repeat while(more commands to send)
     }
    end fork
    end
  |TWS|
  fork again
     -[hidden]->
    start
    partition ProcessConnect {
    :connect()<
    fork
    :managedAccounts()>
    fork again
    :nextValidId()>
    end fork
    }
    partition ProcessCommands {
     repeat
     :command<
     repeat
     :responsePart>
     repeat while(moreParts)
     :responseEnd>
     repeat while (more commands)
    }
    detach
  |Command|
  end fork
  @enduml
  """

  def __init__(
   self,
   host: str,
   port: int,
   clientId: int,
   tracker: Optional[OperationsTracker] = None,
   timeout: float = 60
  ) -> None:
    _logger.debug(f"Will timeout at {timeout} seconds")
    self.accounts: list[str] = []
    Listener.__init__(self, OperationsTracker() if tracker is None else tracker)
    ClientStub.__init__(self, clientId=clientId, ib_wrapper=self)
    self._host = host
    self._port = port
    self._lock = threading.Lock()
    self._lock_counter: int = 0
    self._listener: threading.Thread = threading.Thread(
     target=self.run, name=f"{self.__class__.__name__}::Listener::{clientId}"
    )
    self._commander: threading.Thread = threading.Thread(
      target=self._commandActivator, name=f"{self.__class__.__name__}::Commander::{clientId}",
    )
    self._max_time_cleanup = threading.Timer(timeout, self.stop, args=["Time Exhausted"])
    # self._console_watcher = threading.Thread(
    #  target=self._consoleWatcher, daemon=True, name=f"{self.__class__.__name__}::ConsoleWatcher::{clientId}",
    # )
    # These to migrate to Response Tracker
    self._in_progress: dict[int, list[Any]] = {}

  # def _consoleWatcher(self) -> None:
  #   lastInput = input("Command > ")
  #   while lastInput != self.terminate:
  #     lastInput = input("Command > ")
  #   self.stop("Console Terminated")

  def activate(self) -> None:
    _logger.info(f"Connecting to {self._host}:{self._port} with ClientId: {self.clientId}")
    self.connect(self._host, self._port, self.clientId)  # pyright: ignore
    _logger.info("serverVersion: %s connectionTime: %s" % (self.serverVersion(), self.twsConnectionTime()))
    self._listener.start()
    self._max_time_cleanup.start()
    # if self.terminate:
    #   self._console_watcher.start()

  def wait_for_me(self) -> Optional[dict[str, list[ErrorResponse]]]:
    if not self.isActive():
      self._listener.join()
      self._max_time_cleanup.join()
      return self.responseTracker.errorResults()
    return None

  def stop(self, reason: str = "") -> None:
    _logger.info(f"Stopping because of {reason}")
    super().stop(reason)
    self._max_time_cleanup.cancel()
    self.disconnect()

  def managedAccounts(self, accountsList: str) -> None:
    # Call back from first connection.
    _logger.info(f"Receiving Accounts: {accountsList}")
    self.accounts = accountsList.split(",")
    self.startIfPossible()

  def nextValidId(self, orderId: int) -> None:
    _logger.debug("Updating the nextValidId to: %s", orderId)
    self.responseTracker.syncOpId(orderId)
    self.startIfPossible()

  def startIfPossible(self) -> None:
    _logger.debug(
       f"StartIfPossible() called: {self.responseTracker.isStarted()},"
       f" {self.responseTracker.isInitialized()}, {self.accounts}"
    )
    if not self.responseTracker.isStarted() and self.responseTracker.isInitialized() and self.accounts:
      self.responseTracker.start()
      self._commander.start()

  def _commandActivator(self) -> None:
    try:
      self.runCommands()
      with self._lock:
        _logger.debug("Run Commands is Complete")
        self.responseTracker.requestsComplete()
    except BaseException as exception:
      _logger.critical(exception, exc_info=True)
      raise exception

  def runCommands(self) -> None:
    raise Exception("The Method runCommands() must be implemented")

  def sendMsg(self, msg: str) -> None:
    caller = current_fn_name(1)
    if caller != "startApi":
      self.responseTracker.request(caller, msg)
    super().sendMsg(msg)

  def partialResponse(self, reqId: int, rsp: dict[str, Any]) -> None:
    with self._lock:
      if reqId not in self._in_progress:
        self._in_progress[reqId] = []
      self._in_progress[reqId].append(rsp)

  def completeResponse(self, reqId: int) -> Optional[list[Any]]:
    with self._lock:
      self.responseTracker.complete(SuccessResponse(reqId))
      result = self._in_progress.pop(reqId, [])
    if self.responseTracker.isIdle():
      _logger.debug(f"Tracker found idle at end of response: {reqId}: {current_fn_name(2)}::{current_fn_name(1)}")
      self.stop("Tracker is Idle")
    else:
      _logger.debug("Tracker not Idle")
    return result

  def responsesFor(self, reqId: int) -> list[Any]:
    return self._in_progress.get(reqId, [])
