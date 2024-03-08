from typing import Any
import logging

_logger = logging.getLogger(__name__)


class RecordMeta:
  common_fields: list[str] = ['id', 'at']

  def __init__(self, table: str, own_fields: list[str], db_version: int, logLevel: int = logging.INFO):
    _logger.setLevel(logLevel)
    self.db_version = db_version
    self.table = table
    self.own_fields = own_fields
    self.all_fields = RecordMeta.common_fields + own_fields
    self.counter = "Select count(id) from " + table
    self.selector = "Select "+','.join(self.all_fields) + " from " + table
    self.inserter = 'Insert into ' + table + ' (' + ', '.join(self.all_fields) + ') '
    self.value_inserter = self.inserter + 'values (' + ', '.join(['?'] * len(self.all_fields)) + ');'
    _logger.info(f"Table[{table}] Value Inserter = {self.value_inserter}")
    self.updater = 'Update ' + table + ' set ' + ', '.join([f"{k} = ?" for k in self.all_fields])
    self.deleter = 'Delete from {} where id == ?'.format(self.table)


class Record:
  def __init__(self, id: str, at: int, companion: RecordMeta, *argsv: list[Any]) -> None:
    self.id: str = id
    self.at: int = at
    self.companion: RecordMeta = companion
    for field, value in zip(companion.own_fields, argsv):
      self.__dict__[field] = value

  def values(self) -> tuple[Any]:
    return tuple(self.__dict__[f] for f in self.companion.all_fields)

  def __repr__(self) -> str:
    return str(self.__dict__)
