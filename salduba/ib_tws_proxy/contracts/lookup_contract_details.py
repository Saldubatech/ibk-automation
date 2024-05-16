from typing import Callable, Optional
import logging
import time

from ibapi.contract import Contract, ContractDetails

from salduba.ib_tws_proxy.base_proxy.tws_proxy import BaseProxy
from salduba.ib_tws_proxy.operations import ErrorResponse


_logger = logging.getLogger(__name__)


class LookupContractDetails(BaseProxy):
  def __init__(self,
               targets: list[Contract],
               postProcess: Callable[[Contract, list[dict[str, ContractDetails]]], None],
               host: str,
               port: int,
               clientId: int,
               timeout: float = 15 * 60,
               terminate: Optional[str] = 'quit',
               search_delay: Optional[float] = None
               ) -> None:
    super().__init__(host, port, clientId, timeout=timeout, terminate=terminate)
    self.targets = targets
    self.postProcess = postProcess
    self.search_delay = search_delay
    self.requestedContracts: dict[int, Contract] = {}

  def runCommands(self) -> None:
    _logger.debug(f"Will request {len(self.targets)} contracts: {self.targets}")
    for t in self.targets:
      oid: Optional[int] = self.responseTracker.nextOpId()
      if oid:
        with self._lock:
          _logger.debug(f"Requesting Details for: {t}")
          self.reqContractDetails(oid, t)
          self.requestedContracts[oid] = t
        if self.search_delay:
          time.sleep(self.search_delay)
      else:
        _logger.error(f"Cannot generate OrderId")

  def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> None:
    _logger.debug(f"Received ContractDetails for {reqId}: {contractDetails}")
    self.partialResponse(reqId, {'contractDetails': contractDetails})

  def contractDetailsEnd(self, reqId: int) -> None:
    _logger.debug(f"Received ContractDetailsEnd for {reqId}")
    # print(f"Received ContractDetailsEnd for {reqId}")
    with self._lock:
      contract = self.requestedContracts.get(reqId)
      receivedDetails = self.responsesFor(reqId)
    _logger.debug(f"Found: {receivedDetails} for {contract}")
    if not contract:
      msg = f"Received ContractDetailsEnd for not requested contract with reqId: {reqId}"
      _logger.error(msg)
      raise Exception(msg)
    elif not receivedDetails:
      msg = f"Received ContractDetailsEnd with no received details for: {reqId}"
      _logger.error(msg)
      self.responseTracker.error(ErrorResponse(reqId, 8888, msg, ''))
      raise Exception(msg)
    else:
      self.postProcess(contract, receivedDetails)
      self.completeResponse(reqId)
