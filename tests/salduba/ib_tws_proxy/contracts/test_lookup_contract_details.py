import logging
import os
from pathlib import Path

import pandas as pd
import pytest
from ibapi.contract import Contract, ContractDetails  # pyright: ignore

from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(os.path.join(_tr, "resources/logging.yaml")))
_logger = logging.getLogger(__name__)


def buildContract(symbol: str, secType: str, exchange: str, currency: str) -> Contract:
  contract = Contract()
  contract.symbol = symbol
  contract.secType = secType
  contract.exchange = exchange
  contract.currency = currency
  return contract


host = "127.0.0.1"
port = 7497
appId = 9001


def _postprocessor(contract: Contract, details: list[dict[str, ContractDetails]]) -> None:
  msg = f"Got[{len(details)}] Contracts"
  assert len(details) == 1
  assert contract.symbol == details[0]["contractDetails"].contract.symbol
  assert (
      contract.exchange == details[0]["contractDetails"].contract.exchange
  ), f"Found: {contract.exchange} != {details[0]['contractDetails'].contract.exchange}"
  assert contract.currency == details[0]["contractDetails"].contract.currency
  assert contract.secType == details[0]["contractDetails"].contract.secType
  _logger.debug(msg)


@pytest.mark.tws
def test_one_contract() -> None:
  logging.info("Test Just One")
  probe = buildContract("ACN", "STK", "NASDAQ", "USD")
  underTest = LookupContractDetails(
      [probe],
      _postprocessor,
      host,
      port,
      appId,
      timeout=30,
      search_delay=0.1,
  )
  underTest.activate()
  errors = underTest.wait_for_me()
  assert errors is not None and len(errors['error']) == 0, f"Got errors: {errors}"


@pytest.mark.tws
def test_a_bunch() -> None:
  logging.info("Test A Bunch")
  bunch: pd.DataFrame = \
    pd.read_csv("tests/salduba/ib_tws_proxy/contracts/sample_contracts.csv", index_col="Ticker")  # pyright: ignore
  bunchProbe = \
    [buildContract(r.Symbol, r.IBKType, r.Exchange, r.Currency) for r in bunch.itertuples()]  # type: ignore
  underTest = LookupContractDetails(
      bunchProbe[0:10],
      _postprocessor,
      host,
      port,
      appId,
      15,
      0.1,
  )
  underTest.activate()
  results = underTest.wait_for_me()
  assert results, f"Got results: {results}"
  assert results is not None and len(results['error']) == 0, f"Got errors: {results['error']}"
