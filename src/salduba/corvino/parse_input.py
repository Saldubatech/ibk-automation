import logging
from typing import Optional

import pandas as pd

from salduba.ib_tws_proxy.domain.enumerations import Country, Currency, Exchange, SecType

_logger = logging.getLogger(__name__)


typeTable = {"Equity": SecType.STK}


currencyTable = {
  "SW": Currency.CHF,
  "NA": Currency.EUR,
  "SM": Currency.EUR,
  "IM": Currency.EUR,
  "BB": Currency.EUR,
  "GR": Currency.EUR,
  "FP": Currency.EUR,
  "LN": Currency.GBP,
  "JP": Currency.JPY,
  "AV": Currency.EUR,
  "US": Currency.USD,
}


exchangeTable = {
  "SW": Exchange.EBS,
  "NA": Exchange.AEB,
  "SM": Exchange.BM,
  "IM": Exchange.BVME,
  "BB": Exchange.ENEXT_BE,
  "GR": Exchange.IBIS,
  "FP": Exchange.SBF,
  "LN": Exchange.LSE,
  "JP": Exchange.TSEJ,
  "AV": Exchange.VSE,
  "US": Exchange.ISLAND,
}


def split_ticker(ticker: str) -> list[str]:
  cols = ticker.split(" ")
  cols.append(typeTable.get(cols[-1], cols[-1]))
  return cols


class InputParser:
  additional_columns = ["Symbol", "RawType" "RawCountry", "IbkType"]

  def __init__(self, sheet: str = "Movements"):
    self.sheet = sheet

  @staticmethod
  def _fill_in(frame: pd.DataFrame) -> pd.DataFrame:
    frame.index.rename("TickerIndex", inplace=True)
    frame["Ticker"] = frame.index
    (
      frame["Symbol"],
      frame["Country"],
      frame["RawType"],
      frame["IbkType"],
    ) = zip(*frame.index.map(split_ticker))
    frame.loc[:, "Country"] = frame["Country"].apply(lambda n: Country(n))
    frame.loc[:, "IbkType"] = frame["IbkType"].apply(lambda n: SecType(n))
    if "Currency" not in frame.columns:
      frame.loc[:, "Currency"] = frame["Country"].apply(lambda c: currencyTable.get(c, Currency.UNKNOWN))
    else:
      frame.loc[:, "Currency"] = frame["Currency"].apply(lambda n: Currency(n))
    if len(frame[frame["Currency"] == Currency.UNKNOWN]) > 0:
      raise Exception(f"Cannot Find Currencies for:\n {frame[frame['Currency'] is None]}")
    if "Exchange" not in frame.columns:
      frame.loc[:, "Exchange"] = frame["Country"].apply(lambda c: exchangeTable.get(c, Exchange.UNKNOWN))
    else:
      frame.loc[:, "Exchange"] = frame["Exchange"].apply(lambda n: Exchange(n))
    if len(frame[frame["Exchange"] == Exchange.UNKNOWN]) > 0:
      raise Exception(f"Cannot Find Exchanges for:\n {frame[frame['Exchange'] is None]}")
    if "Exchange 2" in frame.columns:
      frame.rename(columns={"Exchange 2": "Exchange2"}, inplace=True)
    if "Exchange2" not in frame.columns:
      frame.loc[:, "Exchange2"] = frame["Exchange"].apply(
        lambda ex: Exchange.NYSE if ex == Exchange.ISLAND else Exchange.NONE)
    else:
      frame.loc[:, "Exchange2"] = frame["Exchange2"].apply(lambda n: Exchange.NONE if n == "" else Exchange(n))
    frame.rename(columns={"Exchange 2": "Exchange2"}, inplace=True)
    return frame.sort_values("TickerIndex")

  @staticmethod
  def read_excel(movements_path: str, sheet: str = "Movements") -> pd.DataFrame:
    movementsPD: pd.DataFrame = pd.read_excel(
      movements_path,
      sheet,
      usecols=["Ticker", "Trade"],
      index_col="Ticker",
      dtype={"Ticker": str, "Trade": int},
      keep_default_na=False,
    )
    result = InputParser._fill_in(movementsPD)
    return result

  @staticmethod
  def read_full_excel(movements_path: str, sheet: str = "Movements") -> pd.DataFrame:
    movementsPD: pd.DataFrame = pd.read_excel(
      movements_path,
      sheet,
      usecols=[
        "Ticker",
        "ID ISIN",
        "Nombre",
        "Trade",
        "Currency",
        "Exchange",
        "Exchange 2",
      ],
      index_col="Ticker",
      dtype={
        "Ticker": str,
        "ID ISIN": str,
        "Nombre": str,
        "Trade": int,
        "Currency": str,
        "Exchange": str,
        "Exchange 2": str,
      },
      keep_default_na=False,
    )
    if not movementsPD["Exchange"].iloc[0]:
      raise Exception("Exchange is empty for first row. Probably the formulas are not evaluated")
    movementsPD.rename(columns={"Exchange 2": "Exchange2"}, inplace=True)
    result = InputParser._fill_in(movementsPD)
    return result

  @staticmethod
  def read_csv(movements_path: str) -> Optional[pd.DataFrame]:
    csv_columns = [
      "Ticker",
      "Trade"
    ]
    try:
      movementsPD: pd.DataFrame = pd.read_csv(
        movements_path,
        usecols=csv_columns,
        index_col="Ticker",
        keep_default_na=False,
      )
      print(f"#### DF:\n{movementsPD[0:10]}")
      return InputParser._fill_in(movementsPD)
    except ValueError as e:
      _logger.error(f"Trying to read {movements_path} with an error: {e}")
      _logger.error(f"The file requires the following columns: {csv_columns}")
      return None
