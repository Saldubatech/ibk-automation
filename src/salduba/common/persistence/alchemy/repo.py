import logging
from abc import ABC, abstractmethod
from typing import Generic, Iterable, TypeVar

from sqlalchemy import Engine, Integer, String, insert, update
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, Session, mapped_column

_logger: logging.Logger = logging.getLogger(__name__)


class EntityBase(MappedAsDataclass, DeclarativeBase):
  """
  Superclass for all Entities in the system. Entity Classes will be converted to `@dataclass`

  See [Sqlalchemy dataclass support](https://docs.sqlalchemy.org/en/20/orm/dataclasses.html) for details
  """
  rid: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
  at: Mapped[int] = mapped_column(Integer, nullable=False)


R = TypeVar("R", bound=EntityBase)


class Repo(Generic[R], ABC):
  def __init__(self, engine: Engine) -> None:
    self.engine = engine

  @abstractmethod
  def recordClz(self) -> type[R]:
    pass

  def update(self, newValue: R) -> None:
    stmt = update(self.recordClz()).where(EntityBase.rid == newValue.rid).values(**newValue.__dict__)
    with Session(self.engine) as ss:
      ss.execute(stmt)

  def insert(self, records: Iterable[R]) -> None:
    with Session(self.engine) as ss:
      ss.execute(
        insert(self.recordClz()),
        [r.__dict__ for r in records]
      )
