import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy import Engine, ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


def test_one() -> None:
  probe = "STK"
  assert probe == "STK"


class Base(DeclarativeBase):
  pass


class User(Base):
  __tablename__: str = "user_account"
  id: Mapped[int] = mapped_column(primary_key=True)
  name: Mapped[str] = mapped_column(String(30))
  fullname: Mapped[Optional[str]]
  addresses: Mapped[List["Address"]] = relationship(
      back_populates="user", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
      return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(Base):
    __tablename__: str = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, email_address={self.email_address!r})"


def createInMemoryEngine() -> Engine:
  return create_engine("sqlite://", echo=True)


def createSchema() -> Engine:
  engine = createInMemoryEngine()
  Base.metadata.create_all(engine)
  return engine


def createCorvinoEngine() -> Engine:
  return create_engine("")


def test_scratch() -> None:
  createSchema()


def persist_a_few_things() -> Engine:
  engine = createSchema()
  with Session(engine) as session:
    spongebob = User(name="spongebob",
                     fullname="Spongebob Squarepants",
                     addresses=[Address(email_address="spongebob@sqlalchemy.org")]
                     )
    sandy = User(
      name="sandy",
      fullname="Sandy Cheeks",
      addresses=[
        Address(email_address="sandy@sqlalchemy.org"),
        Address(email_address="sandy@squirrelpower.org")
      ]
    )
    patrick = User(name="patrick", fullname="Patrick Star")

    session.add_all([spongebob, sandy, patrick])
    session.commit()
  return engine


def select_a_few_things() -> None:
  engine = persist_a_few_things()
  with Session(engine) as session:
    stmt = select(User).where(User.name.in_(["spongebob", "sandy"]))
    for user in session.scalars(stmt):
      print(f"User: {user}")


if __name__ == '__main__':
  select_a_few_things()
