import logging
import os
import unittest
from typing import Any

import pandas as pd
from ibapi.contract import Contract, ContractDetails

from salduba.ib_tws_proxy.contracts.lookup_contract_details import LookupContractDetails
from salduba.util.logging import init_logging
from salduba.util.tests import testRoot

_maybeTr = testRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(os.path.join(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


def buildContract(symbol: str, secType: str, exchange: str, currency: str) -> Contract:
    contract = Contract()
    contract.symbol = symbol
    contract.secType = secType
    contract.exchange = exchange
    contract.currency = currency
    return contract


class TestLookupContractDetails(unittest.TestCase):
    def __init__(self, *args: *Any, **kwargs: dict[str, Any]) -> None:
        # error: Argument 2 to "__init__" of "TestCase" has incompatible type "**dict[str, dict[str, Any]]"; expected "str"
        super().__init__(*args, **kwargs)  # type: ignore
        self.host = "127.0.0.1"
        self.port = 7497
        self.appId = 9001
        _logger.setLevel(logging.DEBUG)

    def _postprocessor(self, contract: Contract, details: list[dict[str, ContractDetails]]) -> None:
        msg = f"Got[{len(details)}]:  {details} for Contract: {contract.__dict__}"
        assert len(details) == 1
        assert contract.symbol == details[0]["contractDetails"].contract.symbol
        assert (
            contract.exchange == details[0]["contractDetails"].contract.exchange
        ), f"Found: {contract.exchange} != {details[0]['contractDetails'].contract.exchange}"
        assert contract.currency == details[0]["contractDetails"].contract.currency
        assert contract.secType == details[0]["contractDetails"].contract.secType
        _logger.info(msg)

    def test_one_contract(self) -> None:
        logging.info("Test Just One")
        probe = buildContract("ACN", "STK", "NASDAQ", "USD")
        underTest = LookupContractDetails(
            [probe],
            self._postprocessor,
            self.host,
            self.port,
            self.appId,
            timeout=30,
            terminate=None,
            search_delay=0.1,
        )
        underTest.activate()

    def test_a_bunch(self) -> None:
        logging.info("Test A Bunch")
        bunch = pd.read_csv("sample_contracts.csv", index_col="Ticker")
        bunchProbe = [buildContract(r.Symbol, r.IBKType, r.Exchange, r.Currency) for r in bunch.itertuples()]  # type: ignore
        print(f"###: Bunch({len(bunchProbe)})")
        for c in bunchProbe[0:10]:
            print(f"\t###{c}")
        underTest = LookupContractDetails(
            bunchProbe[0:10],
            self._postprocessor,
            self.host,
            self.port,
            self.appId,
            60,
            "q",
            0.1,
        )
        underTest.activate()
