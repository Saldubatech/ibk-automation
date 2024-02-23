from typing import Optional
import sqlite3 as sql
import datetime
import os


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


class ConnectionCursor:
  def __init__(self, conn: sql.Connection) -> None:
    self.connection = conn
    self.cursor: Optional[sql.Cursor] = None

  def __enter__(self) -> sql.Cursor:
    if not self.cursor:
      self.cursor = self.connection.cursor()
    return self.cursor
  
  def __exit__(self, *args) -> None:
    assert self.cursor
    self.cursor.close()
    self.cursor = None

     
class DbVersion:
  def __init__(self, version: int, version_time: int, at: int, current: bool) -> None:
    self.version = version
    self.version_time = version_time
    self.at = at
    self.current = current


class TradingDB:
  def __init__(self, storage_path: str, schema_dir: str, seed_dir: str) -> None:
    self.storage_path: str = storage_path
    self.schema_dir: str = schema_dir
    self.seed_dir: str = seed_dir
    self.conn: Optional[sql.Connection] = None
    self.connection_depth = 0

  def connect(self) -> 'TradingDB':
    if not self.conn:
      self.conn = sql.connect(self.storage_path)
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
    return ConnectionCursor(self.conn)

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

  def ensureVersion(self, v: Optional[int], strict: bool = False) -> Optional[DbVersion]:
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

  def _upgrade_from(self,  current_v: Optional[DbVersion], to: Optional[int] = None) -> Optional[DbVersion]:
    schemas: list[str] = os.listdir(self.schema_dir)
    seeds: list[str] = os.listdir(self.seed_dir)
    schemas.remove('meta.sql')
    seeds.remove('meta.sql')
    unified = sorted(set(schemas + seeds))
    current_name = f"v{current_v.version}.sql" if current_v else None
    till_name = f"v{to}.csv" if to else None
    upgrades = sorted([vn for vn in unified if (not current_name or vn > current_name) and (not till_name or vn <= till_name)])
    with self as db:
      with db.cursor() as crs:
        if not current_v:
          crs.executescript(f"{self.schema_dir}/meta.sql")
          crs.executescript(f"{self.seed_dir}/meta.sql")
        for upgrade in upgrades:
          if upgrade in schemas:
            crs.executescript(f"{self.schema_dir}/{upgrade}")
          if upgrade in seeds:
            crs.executescript(f"{self.seed_dir}/{upgrade}")
      return db.version()
