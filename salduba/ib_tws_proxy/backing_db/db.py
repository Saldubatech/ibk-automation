from typing import Optional, Type
from types import TracebackType
import logging
import datetime
import os
import sqlite3 as sql
import re


class Schema:
  """
  @startuml (id=SCHEMA)
  hide spot
  
  title
  Backing DB Schema
  end title
  
  entity Contract {
    * id: uuid
    * at: datetime
    * status: EnumStr
    * connId: int
    * symbol: str
    * sec_type: str
    last_trade_date_or_contract_month: str
    * strike: float
    right: str
    multiplier: str
    * exchange: str
    * primary_exchange: str
    * currency: str
    local_symbol: str
    trading_class: str
    include_expired: bool
    sec_id_type: str
    sec_id: str
    * description: str
    issuer_id: str    
  }
  
  entity Movement {
    * id: uuid
    * contract: FK
    * at: datetime
    * batch: str
    * ref: str
    * trade: int
    * currency: EnumStr
    * money: int
    override_exchange: str
  }
  
  Movement::contract }o-|| Contract::id
  @enduml
  """


class DbConfig:
  def __init__(self, cfg_dict: dict[str, str]):
    self.storage = cfg_dict['path']
    self.schema_dir = cfg_dict['schemas']
    self.seed_dir = cfg_dict['seed_data']
    self.expected_version = cfg_dict['expected_version']
    self.target_version = cfg_dict['target_version']
    self.version_date = cfg_dict['version_date']
    # if not os.path.isfile(self.storage):
    #   raise Exception(f"{self.storage} file does not exist")
    # elif not os.path.exists(self.schema_dir):
    #   raise Exception(f"Schema Dir: {self.schema_dir} directory does not exist")
    # elif os.path.isfile(self.schema_dir):
    #   raise Exception(f"Schema Dir: {self.schema_dir} seems to be a file, not a directory")
    # elif not os.path.exists(self.seed_dir):
    #   raise Exception(f"Seed Dir: {self.seed_dir} directory does not exist")
    # elif os.path.isfile(self.seed_dir):
    #   raise Exception(f"Seed Dir: {self.seed_dir} seems to be a file, not a directory")


class ConnectionCursor:
  def __init__(self, conn: sql.Connection, nesting: int) -> None:
    self.connection = conn
    self.cursor: Optional[sql.Cursor] = None
    self.nesting = nesting
    self.brand_new = True

  def __enter__(self) -> sql.Cursor:
    if not self.brand_new:
      raise Exception('This Cursor was already used')
    self.brand_new = False
    if not self.cursor:
      self.cursor = self.connection.cursor()
      if self.nesting == 0:
        logging.info("\tSTARTING TRANSACTION")
        self.cursor.execute('BEGIN TRANSACTION;')
    return self.cursor

  def __exit__(self, exctype: Optional[Type[BaseException]],
             excinst: Optional[BaseException],
             exctb: Optional[TracebackType]) -> bool:
    assert self.cursor
    if self.nesting == 0:
      if not exctype:
        logging.info("\tCOMMITTING")
        self.connection.commit()
      else:
        logging.warn(f"\tROLLING BACK because of: {excinst}")
        self.connection.rollback()
    self.cursor.close()
    self.cursor = None
    return False


class DbVersion:
  def __init__(self, version: int, version_time: int, at: int, current: bool) -> None:
    self.version = version
    self.version_time = version_time
    self.at = at
    self.current = current

  def __repr__(self) -> str:
    return str(self.__dict__)


class TradingDB:
  def __init__(self, config: DbConfig) -> None:
    self.config = config
    self.conn: Optional[sql.Connection] = None
    self.connection_depth = 0

  def connect(self) -> 'TradingDB':
    if not self.conn:
      self.conn = sql.connect(self.config.storage)
    self.connection_depth += 1
    return self

  def disconnect(self) -> None:
    assert self.conn and self.connection_depth > 0
    self.connection_depth -= 1
    if self.connection_depth == 0:
      self.conn.close()
      self.conn = None

  def __enter__(self) -> 'TradingDB':
    return self.connect()

  def __exit__(self, *args) -> None:
    self.disconnect()

  def cursor(self) -> ConnectionCursor:
    assert self.conn
    return ConnectionCursor(self.conn, self.connection_depth-1)

  def version(self, v: Optional[int] = None) -> Optional[DbVersion]:
    with self as db:
      with db.cursor() as crs:
        tbls = crs.execute("SELECT name From sqlite_master where name = 'db_info'").fetchone()
        if not tbls:
          rs: Optional[tuple[int, int, int, bool]] = None
        elif v:
          rs = crs.execute(f"select version, version_time, at, current from db_info where current = TRUE and version = {v}").fetchone()
        else:
          rs = crs.execute('select version, version_time, at, current from db_info where current = TRUE').fetchone()
        return DbVersion(rs[0], rs[1], rs[2], rs[3]) if rs else None

  def validate(self, expected_version: int, strict: bool = True) -> bool:
    with self as db:
      with db.cursor() as crs:
        tbls = crs.execute("SELECT name From sqlite_master where name = 'db_info'")
        if not tbls.fetchone():
          return False
        elif strict:
          v = self.version(v=expected_version)
          return v is not None
        else:
          v = self.version()
          return v is not None and v.version >= expected_version

  def ensure_version(self, v: Optional[int], strict: bool = False) -> Optional[DbVersion]:
    with self as db:
        current_v = db.version()
        if strict:
          if current_v and v and current_v.version == v:
            return current_v
          else:
            return None
        else:
          if current_v and (not v or current_v.version >= v):
            return current_v
          else:
            return db._upgrade_from(current_v, v)

  def _update_version_in_cursor(self, cursor: sql.Cursor, v: int) -> Optional[DbVersion]:
    cursor.execute(
      """
      insert into db_info (version, version_time, at, current)
      values (?, unixepoch(?, 'utc'), CURRENT_TIMESTAMP, TRUE);
      """,
      (v, self.config.version_date)
      )
    cursor.execute(
      """
      update db_info set current = FALSE where version <> ?;
      """, (v,)
    )
    return self.version()
        
  def _upgrade_from(self,  current_v: Optional[DbVersion], to: Optional[int] = None) -> Optional[DbVersion]:
    schemas: list[str] = os.listdir(self.config.schema_dir)
    seeds: list[str] = os.listdir(self.config.seed_dir)
    schemas.remove('meta.sql')
    seeds.remove('meta.sql')
    unified = sorted(set(schemas + seeds))
    current_name = "v{:04d}.sql".format(current_v.version) if current_v else 'a'
    till_name = "v{:04d}.sql".format(to) if to else 'z'
    upgrades = sorted([vn for vn in unified if (not current_name or vn > current_name) and (not till_name or vn <= till_name)])
    version = None
    with self as db:
      with db.cursor() as crs:
        if not current_v:
          with open(f"{self.config.schema_dir}/meta.sql", 'r') as meta_schema:
            sch = meta_schema.read()
            crs.executescript(sch)
          with open(f"{self.config.seed_dir}/meta.sql", 'r') as meta_seed:
            seed = meta_seed.read()
            crs.executescript(seed)
        for upgrade in upgrades:
          regex = re.search(r'\d+.sql', upgrade)
          if regex:
            v = int(regex.group()[:-4])
            if upgrade in schemas:
              with open(f"{self.config.schema_dir}/{upgrade}", 'r') as schema:
                sch = schema.read()
                crs.executescript(sch)
            if upgrade in seeds:
              with open(f"{self.config.seed_dir}/{upgrade}", 'r') as seed_file:
                seed = seed_file.read()
                crs.executescript(seed)
            version = self._update_version_in_cursor(crs, v)
    return version
