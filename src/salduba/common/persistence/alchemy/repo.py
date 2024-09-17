import logging
from abc import ABC
from typing import Callable, Generic, Iterable, Optional, TypeVar

import pandas as pd
from sqlalchemy import Integer, String, inspect
# from sqlalchemy.dialects import sqlite
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.query import Query

from salduba.common.persistence.alchemy.db import UnitOfWork

_logger = logging.getLogger(__name__)


class RecordBase(DeclarativeBase):
  rid: Mapped[str] = mapped_column(String(255), primary_key=True)
  at: Mapped[int] = mapped_column(Integer, nullable=False)


R = TypeVar("R", bound=RecordBase)


class RepoOps(Generic[R], ABC):
  def __init__(self, entity: type[R]) -> None:
    self.entity = entity
    self.meta = inspect(entity)
    self.columns = [c.key for c in self.meta.columns]

  def selector(self, decorate: Optional[Callable[[Query[R]], Query[R]]] = None) -> Callable[[UnitOfWork], Query[R]]:
    def rs(uow: UnitOfWork) -> Query[R]:
      with uow.in_unit() as s:
        return decorate(s.query(self.entity)) if decorate else s.query(self.entity)
    return rs

  def find(self, decorate: Optional[Callable[[Query[R]], Query[R]]] = None) -> Callable[[UnitOfWork], Iterable[R]]:
    return lambda uow: self.selector(decorate)(uow).all()

  def find_as_dataframe(self, decorate: Optional[Callable[[Query[R]], Query[R]]] = None) -> Callable[[UnitOfWork], pd.DataFrame]:
    def rs(uow: UnitOfWork) -> pd.DataFrame:
      return pd.DataFrame((r.__dict__ for r in self.find(decorate)(uow)), columns=self.columns)
    return rs

  def find_one(self, decorate: Optional[Callable[[Query[R]], Query[R]]] = None) -> Callable[[UnitOfWork], Optional[R]]:
    return lambda uow: self.selector(decorate)(uow).one_or_none()

  def find_by_id(self, rid: str) -> Callable[[UnitOfWork], Optional[R]]:
    return self.find_one(lambda q: q.where(self.entity.rid == rid))

  def count(self, decorate: Optional[Callable[[Query[R]], Query[R]]] = None) -> Callable[[UnitOfWork], int]:
    return lambda uow: self.selector(decorate)(uow).count()

  def insert(self, records: Iterable[R]) -> Callable[[UnitOfWork], None]:
    def rs(uow: UnitOfWork) -> None:
      with uow.in_unit() as s:
        s.add_all(records)
    return rs

  def insert_one(self, record: R) -> Callable[[UnitOfWork], None]:
    def rs(uow: UnitOfWork) -> None:
      with uow.in_unit() as s:
        s.add(record)
    return rs
