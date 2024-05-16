from enum import StrEnum
from typing import TypeVar, Generic, Callable, Iterable, Any, Optional, Sequence, Tuple
import logging

import pandas as pd

from salduba.ib_tws_proxy.backing_db.record import RecordMeta, Record
from salduba.ib_tws_proxy.backing_db.db import TradingDB

_logger = logging.getLogger(__name__)


class SortDirection(StrEnum):
  ASC = 'ASC'
  DESC = 'DESC'


M = TypeVar('M', bound=RecordMeta)
R = TypeVar('R', bound=Record)


class Repo(Generic[M, R]):
  idClause = '(id = ?)'

  def __init__(self, db: TradingDB, record: M, hydrator: Callable[[Iterable[Any]], R]) -> None:
    self.db = db
    self.record = record
    self.hydrator = hydrator

  def insert_raw(self, records: Iterable[Sequence[Any]]) -> None:
    if records:
      with self.db as db:
        with db.cursor() as crs:
          _logger.debug(f"Inserting with {self.record.value_inserter}")
          _logger.debug(f"with parameters: {records}")
          crs.executemany(self.record.value_inserter, records)
    else:
      _logger.warning("Attempted to insert zero records")

  def insert(self, records: list[R]) -> None:
    self.insert_raw([r.values() for r in records])

  def select_raw(
      self,
      parameters: list[Any],
      conditions: list[str] | None = None,
      sorting: list[Tuple[str, SortDirection]] | None = None) -> list[tuple[Any]]:
    results = []
    if conditions:
      selector = self.record.selector + ' where ' + " and ".join(conditions)
    else:
      selector = self.record.selector
    if sorting:
      query = (selector + ' order by ' + ', '.join([f"{f} {s.value}" for f, s in sorting]) + ';')
    else:
      query = selector + ';'
    _logger.debug(f"[{self.__class__.__name__}] Select Query is:\n\t {query}")
    _logger.debug(f"with parameters: {parameters}")
    with self.db as db:
      with db.cursor() as crs:
        results = crs.execute(query, parameters).fetchall()
    _logger.debug(f"Retrieved {len(results)} records")
    return results

  def count(self, parameters: list[Any], *conditions: str) -> int:
    counter = self.record.counter + ' where ' + ' and '.join(conditions) + ';'
    with self.db as db:
      with db.cursor() as crs:
        count: Optional[tuple[int]] = crs.execute(counter, parameters).fetchone()
    return count[0] if count else 0

  def findById(self, rid: str) -> Optional[R]:
    return self.selectOne([rid], [Repo.idClause])
  def selectOne(
      self,
      parameters: list[Any],
      conditions: list[str]) -> Optional[R]:
    r = self.select(parameters, conditions)
    if len(r) > 1:
      msg = f"Found more than one Record for {self.record.table} with {conditions} || {parameters}"
      _logger.error(msg)
    return r[0] if r else None

  def select(
      self,
      parameters: list[Any],
      conditions: list[str] | None = None,
      sorting: list[Tuple[str, SortDirection]] | None = None
  ) -> list[R]:
    results = self.select_raw(parameters, conditions, sorting)
    return [self.hydrator(*r) for r in results]

  def selectAsDataFrame(
      self,
      parameters: list[Any],
      conditions: list[str] | None = None,
      sorting: list[Tuple[str, SortDirection]] | None = None
  ) -> pd.DataFrame:
    results = self.select_raw(parameters, conditions, sorting)
    return pd.DataFrame(results, columns=self.record.all_fields)

  def update(self, new_value: R) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.record.updater, new_value.values())

  def delete(self, rid: str) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.record.byIdDeleter, (rid,))
