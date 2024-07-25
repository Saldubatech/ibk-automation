import logging
import tempfile
from pathlib import Path
from typing import List, Optional

import pytest
from sqlalchemy import Engine, ForeignKey, String, create_engine
from sqlalchemy.orm import Mapped, mapped_column, relationship

from salduba.common.persistence.alchemy.db import Db
from salduba.common.persistence.alchemy.repo import RecordBase, RepoOps
from salduba.util.logging import init_logging
from salduba.util.tests import findTestsRoot

_maybeTr = findTestsRoot()
_tr = _maybeTr if _maybeTr else "./"
init_logging(Path(_tr, "resources/logging.yaml"))
_logger = logging.getLogger(__name__)


class User(RecordBase):
  __tablename__: str = "user_account"
  name: Mapped[str] = mapped_column(String(30))
  fullname: Mapped[Optional[str]]
  addresses: Mapped[List["Address"]] = relationship(
      back_populates="user", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
      return f"User(rid={self.rid!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(RecordBase):
    __tablename__: str = "address"
    email_address: Mapped[str]
    user_id: Mapped[str] = mapped_column(ForeignKey("user_account.rid"))
    user: Mapped[User] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return f"Address For(user={self.user.rid!r}, email_address={self.email_address!r})"


spongebob = User(rid="spongebob_rid",
                 at=101,
                 name="spongebob",
                 fullname="Spongebob Squarepants",
                 addresses=[Address(rid='sp_addr1', at=101, email_address="spongebob@sqlalchemy.org")]
                 )


sandy = User(
  rid="sandy_rid",
  at=101,
  name="sandy",
  fullname="Sandy Cheeks",
  addresses=[
    Address(rid="addr1", at=101, email_address="sandy@sqlalchemy.org"),
    Address(rid="addr2", at=101, email_address="sandy@squirrelpower.org")
  ]
)

patrick = User(rid="patrick_rid", at=101, name="patrick", fullname="Patrick Star")


records = [spongebob, sandy, patrick]


@pytest.fixture
def setup_db() -> Engine:
  return build_engine()


def build_engine() -> Engine:
  try:
    temp = tempfile.NamedTemporaryFile()
    file_name = Path(temp.name)
    temp.close()
    engine = create_engine(f"sqlite:///{file_name.absolute()}", echo=False)
    RecordBase.metadata.create_all(engine)
    print(f"###### Engine URL: {engine.url}")
    return engine
  except Exception as exc:
    print(f"###### Exception: {exc}")
    raise exc


def test_engine(setup_db: Engine) -> None:
  assert setup_db.dialect.name == "sqlite"
  assert setup_db.url.drivername == "sqlite"


class UserOps(RepoOps[User]):
  def __init__(self) -> None:
    super().__init__(User)


def test_repos_persist_a_few_things() -> None:
  engine = build_engine()
  db = Db(engine)

  underTest = UserOps()

  with db.for_work() as uow:
    underTest.insert(records)(uow)
    r_sandy = underTest.find_by_id("sandy_rid")(uow)
    assert r_sandy
    assert r_sandy.name == 'sandy'

  with db.for_work() as uow:
    result = underTest.find(
      lambda q: q.where(User.name.in_(["spongebob", "sandy"])).order_by(User.name)
      )(uow)
    rl = list(result)
    assert len(rl) == 2
    s_name = rl[0].name
    sp_name = rl[1].name
  assert s_name == 'sandy'
  assert sp_name == 'spongebob'


# def test_base_persist_a_few_things() -> None:
#   engine = build_engine()
#   with Session(engine) as session:
#     q = text("SELECT name FROM sqlite_master WHERE type='table';")
#     rs = session.execute(q).scalars().fetchall()
#     result1 = set(n.upper() for n in rs)
#     probe = [n.upper() for n in ['user_account', 'address'] if n.upper() not in result1]
#     assert not probe, f"Retrieved Tables should include probe: {result1}"

#   with Session(engine) as session:

#     session.add_all(records)
#     session.commit()

#     clause: BinaryExpression[bool] = User.name.in_(["spongebob", "sandy"])

#     stmt = select(User).where(clause).order_by(User.name)
#     result2 = session.scalars(stmt).fetchall()
#     assert len(result2) == 2
#     assert result2[1].name == 'spongebob'
#     assert result2[0].name == 'sandy'
