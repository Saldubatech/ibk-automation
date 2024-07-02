import logging
from enum import StrEnum
from typing import Any, Generic, Iterable, Optional, Sequence, Tuple, Type, TypeVar

import inflection
import pandas as pd

from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.backing_db.record import Record

_logger = logging.getLogger(__name__)


class SortDirection(StrEnum):
  ASC = "ASC"
  DESC = "DESC"


R = TypeVar("R", bound=Record)


class Repo(Generic[R]):

  def __init__(self, db: TradingDB, recordType: Type[R], record_table: str) -> None:
    self.db = db
    self.recordType: Type[R] = recordType
    self.table = record_table
    self.idClause = "rid == ?"
    self.atClause = "at == ?"
    self.counter = "Select count(id) from " + record_table
    self.columns = [inflection.underscore(f) for f in recordType.fields()]
    self.selector = "select " + ", ".join(self.columns) + " from " + record_table
    self.inserter = "Insert into " + record_table + " (" + ", ".join(self.columns) + ") "
    self.value_inserter = self.inserter + "values (" + ", ".join(["?"] * len(self.columns)) + ");"
    self.updater_prefix = "Update " + record_table + " set "
    self.full_updater = self.updater_prefix + ", ".join([f"{k} = ?" for k in self.columns])
    self.byIdDeleter = "Delete from {} where id == ?".format(record_table)
    self.before_or_at_clause = "('at' <= ?)"

  def insert_raw(self, records: Iterable[Sequence[R]]) -> None:
    if records:
      with self.db as db:
        with db.cursor() as crs:
          _logger.debug(f"Inserting with {self.value_inserter}")
          _logger.debug(f"with parameters: {records}")
          crs.executemany(self.value_inserter, records)
    else:
      _logger.warning("Attempted to insert zero records")

  def insert(self, records: list[R]) -> None:
    self.insert_raw([r.values() for r in records])

  def select_raw(
    self,
    parameters: list[Any],
    conditions: list[str] | None = None,
    sorting: list[Tuple[str, SortDirection]] | None = None,
    limit: Optional[int] = None
  ) -> list[tuple[Any]]:
    results = []
    if conditions:
      selector = self.selector + " where " + " and ".join(conditions)
    else:
      selector = self.selector

    if sorting:
      query = selector + " order by " + ", ".join([f"{f} {s.value}" for f, s in sorting]) + ";"
    else:
      query = selector + ";"
    _logger.debug(f"[{self.__class__.__name__}] Select Query is:\n\t {query}")
    _logger.debug(f"with parameters: {parameters}")
    with self.db as db:
      with db.cursor() as crs:
        if limit is None:
          results = crs.execute(query, parameters).fetchall()
        else:
          results = crs.execute(query, parameters).fetchmany(limit)
    _logger.debug(f"Retrieved {len(results)} records")
    return results

  def count(self, parameters: list[Any], *conditions: str) -> int:
    counter = self.counter + " where " + " and ".join(conditions) + ";"
    with self.db as db:
      with db.cursor() as crs:
        count: Optional[tuple[int]] = crs.execute(counter, parameters).fetchone()
    return count[0] if count else 0

  def findById(self, rid: str) -> Optional[R]:
    return self.selectOne([rid], [self.idClause])

  def selectOne(self, parameters: list[Any], conditions: list[str]) -> Optional[R]:
    r = self.select(parameters, conditions)
    if len(r) > 1:
      msg = f"Found more than one Record for {self.table} with {conditions} || {parameters}"
      _logger.error(msg)
    return r[0] if r else None

  def select(
    self,
    parameters: list[Any],
    conditions: list[str] | None = None,
    sorting: list[Tuple[str, SortDirection]] | None = None,
  ) -> list[R]:
    results = self.select_raw(parameters, conditions, sorting)
    return [self.recordType.hydrate(*r) for r in results]

  def selectLast(
    self,
    parameters: list[Any],
    conditions: list[str] | None = None,
    sorting: list[Tuple[str, SortDirection]] | None = None,
    at: Optional[int] = None
  ) -> Optional[R]:
    if at is None:
      result = self.select_raw(parameters, conditions, [('at', SortDirection.DESC)], limit=1)
    else:
      inner_parameters = parameters.copy()
      inner_parameters.append(at)
      conditions_with_time = [] if conditions is None else conditions.copy()
      conditions_with_time.append(self.before_or_at_clause)
      result = self.select_raw(parameters, conditions_with_time, [('at', SortDirection.DESC)], limit=1)
    return None if not result else self.recordType.hydrate(*result[0])

  def selectAsDataFrame(
    self,
    parameters: list[Any],
    conditions: list[str] | None = None,
    sorting: list[Tuple[str, SortDirection]] | None = None,
  ) -> pd.DataFrame:
    results: list[Tuple[Any]] = self.select_raw(parameters, conditions, sorting)
    return pd.DataFrame(results, columns=self.recordType.fields())

  def update(self, new_value: R) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.full_updater, new_value.values())

  def delete(self, rid: str) -> None:
    with self.db as db:
      with db.cursor() as crs:
        crs.execute(self.byIdDeleter, (rid,))
