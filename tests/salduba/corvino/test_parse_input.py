import logging
import os
import unittest

from salduba.corvino.parse_input import InputParser, split_ticker
from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType
from salduba.util.logging import init_logging
from salduba.util.tests import testRoot

_maybeTr = testRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(os.path.join(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


class TestParseInput(unittest.TestCase):
    def test_parse_input_positive(self) -> None:
        probe = "VBK GR Equity"
        result = split_ticker(probe)
        self.assertEqual(4, len(result))
        self.assertEqual("VBK", result[0])
        self.assertEqual("GR", result[1])
        self.assertEqual("Equity", result[2])
        self.assertEqual("STK", result[3])

    def test_parse_input_bad_sec_type(self) -> None:
        probe = "VBK GR BadBad"
        result = split_ticker(probe)
        self.assertEqual(4, len(result))
        self.assertEqual("VBK", result[0])
        self.assertEqual("GR", result[1])
        self.assertEqual("BadBad", result[2])
        self.assertEqual("BadBad", result[3])

    def test_read_excel(self) -> None:
        probe = os.path.join(_tr, "resources/Cervino Rebalance 240503.xlsx")
        # TODO
        result = InputParser.read_excel(probe, "Movements")
        self.assertEqual(109, len(result))
        self.assertEqual(
            set(
                [
                    "ID ISIN",
                    "Nombre",
                    "Trade",
                    "Currency",
                    "Exchange",
                    "Exchange2",
                    "Symbol",
                    "Country",
                    "RawType",
                    "IbkType",
                ]
            ),
            set(result.columns),
        )
        self.assertEqual("2875 JP Equity", result.index[0])
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
            "IbkType": "STK",
        }
        first = result.iloc[0]
        self.assertEqual(expect_in_0, dict(first))

    def test_read_full_excel(self) -> None:
        probe = os.path.join(_tr, "resources/Cervino Rebalance 240503.xlsx")
        # TODO
        try:
            result = InputParser.read_full_excel(probe, "Movements")
            self.assertEqual(109, len(result))
            self.assertEqual(
                set(
                    [
                        "ID ISIN",
                        "Nombre",
                        "Trade",
                        "Currency",
                        "Exchange",
                        "Exchange2",
                        "Symbol",
                        "Country",
                        "RawType",
                        "IbkType",
                    ]
                ),
                set(result.columns),
            )
            self.assertEqual("2875 JP Equity", result.index[0])
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
                "IbkType": "STK",
            }
            first = result.iloc[0]
            self.assertEqual(expect_in_0, dict(first))
        except Exception as exc:
            self.assertEqual(
                "Exchange is empty for first row. Probably the formulas are not evaluated",
                str(exc),
            )

    def test_read_csv(self) -> None:
        probe = os.path.join(_tr, "resources/cervino_rebalance_v2.csv")
        result = InputParser.read_csv(probe)
        self.assertEqual(112, len(result))
        self.assertEqual(
            set(
                [
                    "Symbol",
                    "Nombre",
                    "Trade",
                    "Currency",
                    "Exchange",
                    "Exchange2",
                    "RawType",
                    "Country",
                    "IbkType",
                ]
            ),
            set(result.columns),
        )
        self.assertEqual("2222 JP Equity", result.index[0])
        expect_in_0 = {
            "Nombre": "Kotobuki Spirits Co Ltd",
            "Trade": -2400,
            "Currency": Currency.JPY,
            "Exchange": Exchange.TSEJ,
            "Exchange2": Exchange.NONE,
            "Symbol": "2222",
            "Country": Country.JP,
            "RawType": "Equity",
            "IbkType": SecType.STK,
        }
        first = result.iloc[0]
        self.assertEqual(expect_in_0, dict(first))


if __name__ == "__main__":
    unittest.main()
