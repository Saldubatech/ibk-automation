import dataclasses as dc
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional, Self, Tuple

_logger = logging.getLogger(__name__)


@dataclass
class Record:
  rid: str
  at: int

  @classmethod
  def hydrate(cls, *args) -> Self:  # type: ignore
    return cls(*args)

  @classmethod
  def fields(cls: type[Self]) -> list[str]:
    return [f.name for f in dc.fields(cls)]

  @classmethod
  def own_fields(cls: type[Self]) -> list[str]:
    return cls.fields()[2:]

  @staticmethod
  def caster(v: Optional[Any]) -> Optional[Any]:
    if v is None:
      return None
    elif isinstance(v, Decimal):
      return float(v)
    else:
      return v

  @classmethod
  def from_dict(cls, rid: str, at: int, d: dict[str, Any]) -> Self:
    v = [rid, at] + [d[k] for k in cls.own_fields()]
    return cls.hydrate(*v)

  def values(self) -> Tuple[Any, ...]:
    return tuple(Record.caster(self.__dict__[f]) for f in self.fields())
