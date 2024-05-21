import logging
import os

from salduba.corvino.parse_input import InputParser, split_ticker
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(os.path.join(_tr, "resources/logging.yaml"))
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


def test_read_excel() -> None:
  probe = os.path.join(_tr, "resources/Cervino Rebalance 240503.xlsx")
  # TODO
  result = InputParser.read_excel(probe, "Movements")
  assert 109, len(result)
  assert {
             "Ticker",
             "ID ISIN",
             "Nombre",
             "Trade",
             "Currency",
             "Exchange",
             "Exchange2",
             "Symbol",
             "Country",
             "RawType",
             "IbkType"
  } == set(result.columns)

  assert "2875 JP Equity" == result.index[0]
  expect_in_0 = {
      "ID ISIN": "JP3613000003",
      "Nombre": "Toyo Suisan Kaisha Ltd",
      "Trade": 600,
      "Currency": str(Currency.JPY),
      "Exchange": str(Exchange.TSEJ),
      "Exchange2": str(Exchange.NONE),
      "Symbol": "2875",
      "Country": "JP",
      "RawType": "Equity",
      "IbkType": "STK",
      'Ticker': '2875 JP Equity',
    }
  first = result.iloc[0]
  assert expect_in_0 == dict(first)


def test_read_full_excel() -> None:
  probe = os.path.join(_tr, "resources/Cervino Rebalance 240503.xlsx")
  # TODO
  try:
    result = InputParser.read_full_excel(probe, "Movements")
    assert 109, len(result)
    assert {
               "ID ISIN",
               "Nombre",
               "Trade",
               "Currency",
               "Exchange",
               "Exchange2",
               "Symbol",
               "Country",
               "RawType",
               "IbkType"
               } == set(result.columns)
    assert "2875 JP Equity" == result.index[0]
    expect_in_0 = {
       "ID ISIN": "JP3613000003",
       "Nombre": "Toyo Suisan Kaisha Ltd",
       "Trade": 600,
       "Currency": Currency.JPY,
       "Exchange": Exchange.TSEJ,
       "Exchange2": Exchange.NONE,
       "Symbol": "2875",
       "Country": "JP",
       "RawType": "Equity",
       "IbkType": "STK"
    }
    first = result.iloc[0]
    assert expect_in_0 == dict(first)
  except Exception as exc:
    assert "Exchange is empty for first row. Probably the formulas are not evaluated" == str(exc)


def test_read_csv() -> None:
    probe = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
    result = InputParser.read_csv(probe)
    assert 112 == len(result)
    assert {
        "Symbol",
        "Nombre",
        "Trade",
        "Currency",
        "Exchange",
        "Exchange2",
        "RawType",
        "Country",
        "IbkType",
        "Ticker"
    } == set(result.columns)
    assert "2222 JP Equity" == result.index[0]
    expect_in_0 = {
        "Nombre": "Kotobuki Spirits Co Ltd",
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
    first = result.iloc[0]
    assert expect_in_0 == dict(first)
