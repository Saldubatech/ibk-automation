from typing import TypeVar, Generic, Callable, Iterable, Any
import logging

import pandas as pd

from salduba.ib_tws_proxy.backing_db.record import RecordMeta, Record
from salduba.ib_tws_proxy.backing_db.db import TradingDB

_logger = logging.getLogger(__name__)

M = TypeVar('M', bound=RecordMeta)
R = TypeVar('R', bound=Record)


class Repo(Generic[M, R]):
  def __init__(self, db: TradingDB, record: M, hydrator: Callable[[Iterable[Any]], R], logLevel: int = logging.INFO) -> None:
    self.db = db
    self.record = record
    self.hydrator = hydrator
    _logger.setLevel(logLevel)

  def insert_raw(self, records: Iterable[Iterable[Any]]) -> None:
    if records:
      with self.db as db:
        with db.cursor() as crs:
          _logger.debug(f"Inserting with {self.record.value_inserter}")
          _logger.debug(f"with parameters: {records}")
          crs.executemany(self.record.value_inserter, records)
    else:
      _logger.warn("Attempted to insert zero records")

  def insert(self, records: list[R]) -> None:
    self.insert_raw([r.values() for r in records])

  def select_raw(self, parameters: list[Any], *conditions: str) -> list[tuple[Any]]:
    results = []
    query = self.record.selector + ' where ' + ' and '.join(conditions) + ';'
    with self.db as db:
      with db.cursor() as crs:
        results = crs.execute(query, parameters).fetchall()
    return results

  def select(self, parameters: list[Any], *conditions: str) -> list[R]:
    results = self.select_raw(parameters, *conditions)
    return [self.hydrator(r) for r in results]

  def selectAsDataFrame(self, parameters: list[Any], *conditions: str) -> pd.DataFrame:
    results = self.select_raw(parameters, *conditions)
    return pd.DataFrame(results, columns=self.record.all_fields)

  def update(self, new_value: R) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.record.updater, new_value.values())

  def delete(self, id: str) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.record.deleter, (id,))
