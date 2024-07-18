import datetime
import logging
from enum import StrEnum
from typing import Callable, Optional

from ibapi.utils import current_fn_name  # pyright: ignore

_logger = logging.getLogger(__name__)


class Request:
  def __init__(self, fromCaller: str, msg: str) -> None:
    self.fromCaller = fromCaller
    self.msg = msg
    self.at = datetime.datetime.now()

  def __repr__(self) -> str:
    return repr(self.__dict__)


class RequestResult(StrEnum):
  OK = "OK"
  NOK = "NOK"


class Response:
  def __init__(self, opId: int, info: str = "") -> None:
    self.opId = opId
    self.at = datetime.datetime.now()
    self.info = info

  def __repr__(self) -> str:
    return repr(self.__dict__)


class SuccessResponse(Response):
  def __init__(self, opId: int, info: str = "") -> None:
    super().__init__(opId, info)


class ErrorResponse(Response):
  def __init__(
    self,
    opId: int,
    errorCode: int,
    errorString: str,
    advancedOrderRejectJson: str,
  ) -> None:
    super().__init__(opId)
    self.errorCode = errorCode
    self.errorString = errorString
    self.advancedOrderRejectJson = advancedOrderRejectJson


class Operation:
  def __init__(self, opId: int, request: Request, error: Optional[ErrorResponse] = None) -> None:
    self.opId = opId
    self.request = request
    self.responses: list[SuccessResponse] = []
    self.error: Optional[ErrorResponse] = None

  def __repr__(self) -> str:
    return repr(self.__dict__)


class OperationState(StrEnum):
  NEW = "NEW"
  ACTIVE = "ACTIVE"
  IDLE = "IDLE"
  TIMEOUT = "TIMEOUT"
  ERRORED = "ERRORED"


class OperationsTracker:
  max_idle = 3000  # msecs
  info_only = [399]

  def __init__(self, logLevel: int = logging.DEBUG) -> None:
    self.status = OperationState.NEW
    self.pending: dict[int, Operation] = {}
    self.success: list[Operation] = []
    self.errors: list[Operation] = []
    self.info: list[Operation] = []
    self.started = False
    self.requests_complete = False
    self._opId: int = -1  # Unique Id for each request, -1 means not initialized
    #  self._lock = threading.Lock()
    _logger.setLevel(logLevel)

  def _unsafeIsStarted(self) -> bool:
    return self.started and (len(self.success) + len(self.errors) + len(self.pending) > 0)

  def isInitialized(self) -> bool:
    return self._opId != -1

  def isStarted(self) -> bool:
    r = self._unsafeIsStarted()
    return r

  def dump(self, lg: Callable[[str], None]) -> None:
    lg(f"From: {current_fn_name(2)}:{current_fn_name(1)}")
    lg(f"Is Started: {self.started}")
    lg(f"Success: {len(self.success)}")
    lg(f"Errors: {len(self.errors)}")
    lg(f"Pending: {len(self.pending)}")

  def isIdle(self) -> bool:
    r = self.requests_complete and self._unsafeIsStarted() and len(self.pending) == 0
    #     and  elapsed > OperationsTracker.max_idle)
    if r:
      self.status = OperationState.IDLE
    return r

  def start(self) -> None:
    self.status = OperationState.ACTIVE
    self.started = True

  def requestsComplete(self) -> None:
    self.requests_complete = True

  def syncOpId(self, newValue: int) -> None:
    self._opId = newValue

  def unsafeNextOpId(self) -> Optional[int]:
    # This may "waste" request Id's, it may be replaced by a "peek" and "advance" pair.
    if self._opId != -1:
      oid = self._opId
      self._opId += 1
    else:
      oid = None
    return oid

  def nextOpId(self) -> int:
    #  with self._lock:
    #    _logger.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    oid = self.unsafeNextOpId()
    if not oid:
      raise Exception("Trying to get a request Id before available")
    #  _logger.debug("Released Lock")
    return oid

  def request(self, fromCaller: str, msg: str) -> None:
    #  with self._lock:
    #    _logger.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    rId = self._opId - 1  # last one used
    _logger.debug(f"REQUEST: {rId} from {current_fn_name(2)}::{current_fn_name(1)}")
    if rId not in self.pending.keys():
      self.pending[rId] = Operation(rId, Request(fromCaller, msg))
    else:
      _logger.warning(f"Duplicate request Id: {rId} from {fromCaller} with {msg}")
    #  _logger.debug("Released Lock")

  def response(self, rs: SuccessResponse) -> None:
    #  with self._lock:
    #    _logger.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    if rs.opId not in self.pending.keys():
      raise Exception(
        f"Response for unknown request [{current_fn_name(2)}::{current_fn_name(1)}]:"
        + f"{rs} with pending: {self.pending}"
      )
    else:
      self.pending[rs.opId].responses.append(rs)
    #  _logger.debug("Released Lock")

  def complete(self, rs: SuccessResponse) -> None:
    # with self._lock:
    #  _logger.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    self.response(rs)
    self.success.append(self.pending[rs.opId])
    _logger.debug(f"COMPLETE {rs.opId} from {current_fn_name(2)}::{current_fn_name(1)}")
    del self.pending[rs.opId]
    # _logger.debug("Released Lock")

  def error(self, error: ErrorResponse) -> None:
    # with self._lock:
    #  _logger.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    if error.opId in self.pending.keys():
      op = self.pending[error.opId]
      op.error = error
      if error.errorCode in OperationsTracker.info_only:
        self.info.append(op)
        _logger.info(f"{error.opId}")
      else:
        self.errors.append(op)
        _logger.error(f"ERROR {error.opId} from {current_fn_name(2)}::{current_fn_name(1)}")
      del self.pending[error.opId]
    else:
      if error.errorCode == 502:
        self.errors.append(
          Operation(
            error.opId,
            Request("",
                    "Trying to connect to TWS"),
            ErrorResponse(
              error.opId,
              error.errorCode,
              error.errorString,
              error.advancedOrderRejectJson)))
        raise Exception(error.errorString)
      else:
        raise Exception(f"Response for unknown request: {error}")
    # _logger.debug("Released Lock")

  def errorResults(self) -> dict[str, list[ErrorResponse]]:
    return {
      "info": [i.error for i in self.info if i.error],
      "error": [e.error for e in self.errors if e.error]
    }


class OpStatus(StrEnum):
  """
  @startuml (id=OPERATION_STATE)
  title
  Operation Lifecycle
  end title

  state "NEW" as NEW<<start>>

  state ACTIVE {
    state INVOKED
    state ACKNOWLEDGED
    state PART_ANSWERED
  }
  state COMPLETE {
    state SUCCESS
    state FAIL
    state TIMEOUT
  }

  NEW --> INVOKED
  NEW --> ACKNOWLEDGED
  NEW --> PART_ANSWERED
  INVOKED --> ACKNOWLEDGED
  INVOKED --> PART_ANSWERED
  ACKNOWLEDGED -> PART_ANSWERED
  ACKNOWLEDGED --> SUCCESS
  ACKNOWLEDGED --> FAIL
  PART_ANSWERED --> SUCCESS
  PART_ANSWERED --> PART_ANSWERED
  PART_ANSWERED --> FAIL
  INVOKED --> TIMEOUT
  INVOKED --> SUCCESS
  INVOKED --> FAIL

  TIMEOUT --> [*]
  SUCCESS --> [*]
  FAIL --> [*]
  @enduml
  """

  NEW = "0_NEW"
  INVOKED = "1_INVOKED"
  ACKNOWLEDGED = "2_ACKNOWLEDGED"
  PART_ANSWERED = "3_PART_ANSWERED"
  SUCCESS = "4_SUCCESS"
  FAIL = "5_FAIL"
  TIMEOUT = "6_TIMEOUT"
  ARCHIVED = "7_ARCHIVED"
