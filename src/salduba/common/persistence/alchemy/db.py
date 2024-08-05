from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import ExecutableDDLElement, MetaData, create_engine, create_mock_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


class UnitOfWork:
  def __init__(self, session: Session) -> None:
    self.session: Session = session

  @contextmanager
  def in_unit(self) -> Generator[Session, Any, None]:
    try:
      yield self.session.__enter__()
    except Exception as exc:
      self.abandon()
      raise exc
    finally:
      self.checkpoint()

  def checkpoint(self) -> None:
    if self.session and self.session.is_active:
      self.session.commit()
    else:
      raise Exception("Cannot commit an inactive UnitOfWork")

  def abandon(self) -> None:
    if self.session.is_active:
      self.session.rollback()
      self.session.close()


class Db:
  def __init__(self, engine: Engine) -> None:
    self.engine = engine
    self.session: Optional[Session] = None

  @classmethod
  def from_url(cls, url: str, echo: bool = False) -> 'Db':
    return Db(create_engine(url, echo=echo))

  @contextmanager
  def for_work(self) -> Generator[UnitOfWork, Any, None]:
    try:
      if not self.session:
        # expire_on_commit=False is needed to be able to use objects after a commit.
        self.session = Session(self.engine, expire_on_commit=False)
      yield UnitOfWork(self.session)
    except Exception as exc:
      if self.session and self.session.is_active:
        self.session.rollback()
        # self.session.__exit__(type_, value, traceback)
        self.session.close()
      self.session = None
      raise exc
    finally:
      if self.session and self.session.is_active:
        self.session.commit()
        self.session.close()
      self.session = None

  def print_schema(self, metadata: MetaData) -> None:
    def dump(sql: ExecutableDDLElement, *multi_params: Any, **params: Any) -> None:
      print(sql.compile(dialect=self.engine.dialect))
    engine = create_mock_engine(f'{self.engine.url.drivername}://', strategy='mock', executor=dump)
    metadata.create_all(engine, checkfirst=False)
