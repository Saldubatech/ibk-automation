from typing import Optional
from enum import StrEnum
import datetime
import threading
import logging

from ibapi.utils import (
    current_fn_name
)


class Request:
  def __init__(self, fromCaller: str, msg: str) -> None:
    self.fromCaller = fromCaller
    self.msg = msg
    self.at = datetime.datetime.now()

  def __repr__(self) -> str:
    return repr(self.__dict__)


class RequestResult(StrEnum):
  OK = 'OK'
  NOK = 'NOK'

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
  def __init__(self, opId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str) -> None:
    super().__init__(opId)
    self.errorCode = errorCode
    self.errorString = errorString
    self.advancedOrderRejectJson = advancedOrderRejectJson


class Operation:
  def __init__(self, opId: int, request: Request) -> None:
    self.opId = opId
    self.request = request
    self.responses: list[SuccessResponse] = []
    self.error: Optional[ErrorResponse] = None

  def __repr__(self) -> str:
    return repr(self.__dict__)


class OperationsTracker:
  def __init__(self) -> None:
    self.pending: dict[int, Operation] = {}
    self.success: list[Operation] = []
    self.errors: list[Operation] = []
    self.started = False
    self._opId: int = -1  # Unique Id for each request, -1 means not initialized
    #    self._lock = threading.Lock()

  def _unsafeIsStarted(self) -> bool:
      return self.started and (len(self.success) + len(self.errors) + len(self.pending) > 0)

  def isStarted(self) -> bool:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    r = self._unsafeIsStarted()
    #    logging.debug("Released Lock")
    return r

  def isIdle(self) -> bool:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    r = self._unsafeIsStarted() and len(self.pending) == 0
    #    logging.debug("Released Lock")
    return r

  def start(self) -> None:
    #    with self._lock:
    #     logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    self.started = True
    #    logging.debug("Released Lock")

  def syncOpId(self, newValue: int) -> None:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    self._opId = newValue
    #    logging.debug("Released Lock")

  def unsafeNextOpId(self) -> int:
    # This may "waste" request Id's, it may be replaced by a "peek" and "advance" pair.
    if self._opId != -1:
      oid = self._opId
      self._opId += 1
    else:
      raise Exception("Trying to get a request Id before available")    
    return oid

  def nextOpId(self) -> int:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    oid = self.unsafeNextOpId()
    #    logging.debug("Released Lock")
    return oid

  def request(self, fromCaller: str, msg: str) -> None:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    rId = self._opId - 1 # last one used
    logging.info(f"Recording request: {rId}")
    if rId not in self.pending.keys():
      self.pending[rId] = Operation(rId, Request(fromCaller, msg))
    else:
      raise Exception(f"Duplicate request Id: {rId} from {fromCaller} with {msg}")
    #    logging.debug("Released Lock")

  def response(self, rs: SuccessResponse) -> None:
    #    with self._lock:
    #      logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")      
    if rs.opId not in self.pending.keys():
      raise Exception(f"Response for unknown request [{current_fn_name(2)}::{current_fn_name(1)}]: {rs} with pending: {self.pending}")
    else:
      self.pending[rs.opId].responses.append(rs)
    #    logging.debug("Released Lock")

  def complete(self, rs: SuccessResponse) -> None:
    # with self._lock:
    #  logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    self.response(rs)
    self.success.append(self.pending[rs.opId])
    logging.info(f"Removing with complete {rs.opId} from {current_fn_name(2)}::{current_fn_name(1)}")
    del self.pending[rs.opId]
    # logging.debug("Released Lock")

  def error(self, error: ErrorResponse) -> None:
    # with self._lock:
    #  logging.debug(f"Acquired Lock from {current_fn_name(1)}::{current_fn_name(0)}")
    if error.opId not in self.pending.keys():
      raise Exception(f"Response for unknown request: {error}")
    else:
      op = self.pending[error.opId]
      op.error = error
      self.errors.append(op)
      logging.info(f"Removing with error {error.opId} from {current_fn_name(2)}::{current_fn_name(1)}")
      del self.pending[error.opId]
    # logging.debug("Released Lock")


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
  NEW = '0_NEW'
  INVOKED = '1_INVOKED'
  ACKNOWLEDGED = '2_ACKNOWLEDGED'
  PART_ANSWERED = '3_PART_ANSWERED'
  SUCCESS = '4_SUCCESS'
  FAIL = '5_FAIL'
  TIMEOUT = '6_TIMEOUT'
  ARCHIVED = '7_ARCHIVED'
