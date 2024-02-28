from typing import Optional
from enum import StrEnum

import pandas as pd


class Currency(StrEnum):
  EUR = 'EUR'
  USD = 'USD'
  JPY = 'JPY'


class Movement:

  @staticmethod
  def fromFile(movements_path: str, batch: str) -> dict[str, 'Movement']:
    movementsPD: pd.DataFrame = pd.read_csv(movements_path, index_col='Ticker').sort_values('Ticker').drop('NOTHING', axis=1)  # type: ignore
    movementsPD['Trade'] = movementsPD['Trade'].map(lambda tr : int(tr.replace(',', '')))  # type: ignore
    movementsPD['Id'] = movementsPD['Id'].map(lambda id : int(id))    # type: ignore
    movementsPD['Money'] = movementsPD['Money'].map(lambda m : int(m.replace(',', '')))  # type: ignore
    movementsPD = movementsPD[movementsPD['Trade'] != 0]

    return {
      r['Nombre'].upper() :  Movement(  # type: ignore
        batch,
        r['Id'],   # type: ignore
        r['Nombre'],   # type: ignore
        r['Trade'],   # type: ignore
        r['Currency'],   # type: ignore
        r['Money'],  # type: ignore
        overrideExchange='SMART'
      )
      for idx, r in movementsPD.reset_index().iterrows()  # type: ignore
    }

  def __init__(self,
               batch: str,
               movementRef: int,
               name: str,
               trade: int,
               currency: Currency,
               money: int,
               overrideExchange: Optional[str] = None) -> None:
    self.batch = batch
    self.ref = movementRef
    self.overrideExchange = overrideExchange
    self.name = name
    self.trade = trade
    self.currency = currency
    self.money = money
    self.price = round(-float(money)/float(trade), 2)
    self.orderRef: str = f"{self.batch}::{self.name}::{self.ref}"
    self.orderId: int = hash(str)

  def __repr__(self) -> str:
    return repr(self.__dict__)