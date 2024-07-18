import logging
import os
from pathlib import Path

from salduba.corvino.io.parse_input import InputParser, split_ticker
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


def test_parse_input_positive() -> None:
    probe = "VBK GR Equity"
    result = split_ticker(probe)
    assert 4, len(result)
    assert "VBK" == result[0]
    assert "GR" == result[1]
    assert "Equity" == result[2]
    assert "STK" == result[3]


def test_parse_input_bad_sec_type() -> None:
  probe = "VBK GR BadBad"
  result = split_ticker(probe)
  assert 4, len(result)
  assert "VBK" == result[0]
  assert "GR" == result[1]
  assert "BadBad" == result[2]
  assert "BadBad" == result[3]


def test_read_csv_minimal() -> None:
  probe = os.path.join(_tr, "resources/cervino_rebalance_v2_minimal.csv")
  result = InputParser.read_csv(probe)
  assert result is not None
  assert 112 == len(result)
  assert [
      "Trade",
      "Ticker",
      "Symbol",
      "Country",
      "RawType",
      "IbkType",
      "Currency",
      "Exchange",
      "Exchange2"
   ] == list(result.columns)
  assert "2222 JP Equity" == result.index[0]  # pyright: ignore
  expect_in_0 = {
      "Trade": -2400,
      "Currency": str(Currency.JPY),
      "Exchange": str(Exchange.TSEJ),
      "Exchange2": str(Exchange.NONE),
      "Symbol": "2222",
      "Country": str(Country.JP),
      "RawType": "Equity",
      "IbkType": str(SecType.STK),
      'Ticker': '2222 JP Equity'
  }
  first = result.iloc[0]  # pyright: ignore
  assert expect_in_0 == dict(first)  # pyright: ignore


def test_input_rows_from_excel() -> None:
  probe = os.path.join(_tr, "resources/Cervino Rebalance 240503 minimal.xlsx")
  result = InputParser.input_rows_from(probe, "Movements")
  assert 109, len(result)
  assert "2875 JP Equity" == result[0].ticker
  expect_in_0 = {
    "trade": 600,
    "currency": Currency.JPY,
    "exchange": Exchange.TSEJ,
    "exchange2": Exchange.NONE,
    "symbol": "2875",
    "country": "JP",
    "raw_type": "Equity",
    "ibk_type": "STK",
    'ticker': '2875 JP Equity'
  }
  assert expect_in_0 == result[0].__dict__


def test_input_rows_from_csv() -> None:
  probe = os.path.join(_tr, "resources/cervino_rebalance_v2_minimal.csv")
  result = InputParser.input_rows_from(probe, "Movements")
  assert 109, len(result)
  assert "2222 JP Equity" == result[0].ticker
  expect_in_0 = {
      "trade": -2400,
      "currency": Currency.JPY,
      "exchange": Exchange.TSEJ,
      "exchange2": Exchange.NONE,
      "symbol": "2222",
      "country": Country.JP,
      "raw_type": "Equity",
      "ibk_type": SecType.STK,
      'ticker': '2222 JP Equity'
  }
  assert expect_in_0 == result[0].__dict__


def test_read_excel_minimal() -> None:
  probe = os.path.join(_tr, "resources/Cervino Rebalance 240503 minimal.xlsx")
  # TODO
  result = InputParser.read_excel(probe, "Movements")
  assert 109, len(result)
  assert [
      "Trade",
      "Ticker",
      "Symbol",
      "Country",
      "RawType",
      "IbkType",
      "Currency",
      "Exchange",
      "Exchange2"
   ] == list(result.columns)

  assert "2875 JP Equity" == result.index[0]  # pyright: ignore
  expect_in_0 = {
      "Trade": 600,
      "Currency": str(Currency.JPY),
      "Exchange": str(Exchange.TSEJ),
      "Exchange2": str(Exchange.NONE),
      "Symbol": "2875",
      "Country": "JP",
      "RawType": "Equity",
      "IbkType": "STK",
      'Ticker': '2875 JP Equity'
    }
  first = result.iloc[0]  # pyright: ignore
  assert expect_in_0 == dict(first)  # pyright: ignore
