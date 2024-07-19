import datetime
import logging
import re
import sqlite3 as sql
import traceback
from importlib import resources as lib_res
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import TracebackType
from typing import Optional, Type

from salduba.common.configuration import DbConfig

_logger = logging.getLogger(__name__)


# class DbConfig:
#   def __init__(self, cfg_dict: dict[str, str]):
#     self.storage = cfg_dict["path"]
#     self.schema_dir = cfg_dict["schemas"]
#     self.seed_dir = cfg_dict["seed_data"]
#     self.expected_version = int(cfg_dict["expected_version"])
#     self.target_version = int(cfg_dict["target_version"])
#     self.version_date = cfg_dict["version_date"]
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
      raise Exception("This Cursor was already used")
    self.brand_new = False
    if not self.cursor:
      self.cursor = self.connection.cursor()
      if self.nesting == 0:
        _logger.debug("\tSTARTING TRANSACTION")
        self.cursor.execute("BEGIN TRANSACTION;")
    return self.cursor

  def __exit__(
    self,
    exctype: Optional[Type[BaseException]],
    excinst: Optional[BaseException],
    exctb: Optional[TracebackType],
  ) -> bool:
    assert self.cursor
    rs = True
    if self.nesting == 0:
      if not exctype:
        _logger.debug("\tCOMMITTING")
        self.connection.commit()
        rs = True
      else:
        _logger.error(f"\tROLLING BACK because of: {excinst}\n\t{exctb}")
        for line in traceback.format_exception(excinst):
          _logger.error(line)
        self.connection.rollback()
        rs = False
    self.cursor.close()
    self.cursor = None
    return rs


class DbVersion:
  def __init__(self, version: int, version_time: int, at: int, current: bool) -> None:
    self.version = version
    self.version_time = version_time
    self.at = at
    self.current = current

  def __repr__(self) -> str:
    return str(self.__dict__)


class TradingDB:
  def __init__(self, config: DbConfig, use_tmp_file: bool = False) -> None:
    self.config: DbConfig = config
    self.conn: Optional[sql.Connection] = None
    self.connection_depth = 0
    if use_tmp_file:
      tmp_file = NamedTemporaryFile()
      tmp_file.close()
      self.storage = Path(tmp_file.name)
    else:
      self.storage = config.storage_path

  def connect(self) -> "TradingDB":
    if not self.conn:
      self.conn = sql.connect(self.storage)
    self.connection_depth += 1
    return self

  def disconnect(self) -> None:
    assert self.conn and self.connection_depth > 0
    self.connection_depth -= 1
    if self.connection_depth == 0:
      self.conn.close()
      self.conn = None

  def __enter__(self) -> "TradingDB":
    return self.connect()

  def __exit__(self, *args) -> None:  # type: ignore
    self.disconnect()

  def cursor(self) -> ConnectionCursor:
    assert self.conn
    return ConnectionCursor(self.conn, self.connection_depth - 1)

  def configure(self) -> Optional[DbVersion]:
    _logger.debug("Entering Configure")
    rs = None
    if not self.storage.is_file():
      self.storage.touch()

    dbV = self.version()
    if dbV:
      _logger.debug(f"VERSION AT: {dbV.version}")
      current_v = dbV.version
    else:
      _logger.info("No Db Version Found, assuming 0")
      current_v = 0
    if current_v == self.config.min_required_version:
      _logger.info(f"Db Version already at target: {self.config.min_required_version}")
    else:
      _logger.info(f"Upgrading Db Version from {current_v} to {self.config.min_required_version}")
      rs = self.ensure_version(self.config.min_required_version)
    return rs

  def version(self, v: Optional[int] = None) -> Optional[DbVersion]:
    rs: Optional[tuple[int, int, int, bool]] = None
    with self as db:
      with db.cursor() as crs:
        tables = crs.execute("SELECT name From sqlite_master where name = 'db_info'").fetchone()
        if not tables:
          rs = None
        elif v:
          rs = crs.execute(
            f"""
          select
            version, version_time, at, current from db_info
          where current = TRUE and version = {v}
          """
          ).fetchone()
        else:
          rs = crs.execute("select version, version_time, at, current from db_info where current = TRUE").fetchone()
    _logger.error(F"VERSION FOUND: {rs}")
    return DbVersion(rs[0], rs[1], rs[2], rs[3]) if rs else None

  def validate(self, expected_version: int, strict: bool = True) -> bool:
    rs = False
    with self as db:
      with db.cursor() as crs:
        tbls = crs.execute("SELECT name From sqlite_master where name = 'db_info'")
        if not tbls.fetchone():
          rs = expected_version == 0
        elif strict:
          v = self.version(v=expected_version)
          rs = v is not None
        else:
          v = self.version()
          rs = v is not None and v.version >= expected_version
    return rs

  def ensure_version(self, v: Optional[int], strict: bool = False) -> Optional[DbVersion]:
    current_v = None
    with self as db:
      with db.cursor() as _:
        current_v = db.version()
        _logger.info(f"Current Version: {current_v}")
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
    _logger.debug(f"Upgrading with target: {v}")
    inserter = """
    insert into db_info (version, version_time, at, current)
    values (?, ?, CURRENT_TIMESTAMP, TRUE);"""
    _logger.debug(f"New Version Insertion: {inserter}")
    insert_params = [v, int(datetime.datetime.strptime(self.config.version_date, "%Y-%m-%d %H:%M:%S.%f").timestamp())]
    _logger.debug(f"\tWith params: {insert_params}")
    try:
      cursor.execute(inserter, insert_params)
    except sql.OperationalError as ex:
      _logger.error(f"Version Inserting Failed: {ex}")

    obsoleter = "update db_info set current = FALSE where version <> ?;"
    _logger.debug(f"Obsoleting with {obsoleter}")
    obsolete_params = [v]
    _logger.debug(f"\tWith params {obsolete_params}")
    try:
      cursor.execute(obsoleter, obsolete_params)
    except sql.OperationalError as ex:
      _logger.error(f"Version Obsolete  Failed: {ex}")
    return self.version()

  def _upgrade_from(self, current_v: Optional[DbVersion], to: Optional[int] = None) -> Optional[DbVersion]:
    schemas: dict[str, Path] = {}
    meta_schema: Optional[Path] = None
    for sch in self.config.db_schemata:
      with lib_res.as_file(sch) as schema:
        if schema.name != 'meta.sql':
          schemas[schema.name] = schema.absolute()
        else:
          meta_schema = schema.absolute()
    _logger.debug(f"Schemas: {schemas}")
    seeds: dict[str, Path] = {}
    meta_seed: Optional[Path] = None
    for sd in self.config.db_seeds:
      with lib_res.as_file(sd) as seed:
        if seed.name != "meta.sql":
          seeds[seed.name] = seed.absolute()
        else:
          meta_seed = seed.absolute()
    unified: list[str] = sorted(set(schemas.keys()).union(set(seeds.keys())))
    current_name = "v{:04d}.sql".format(current_v.version) if current_v else "a"
    till_name = "v{:04d}.sql".format(to) if to else "z"
    upgrades: list[str] = sorted(
      [vn for vn in unified if (not current_name or vn > current_name) and (not till_name or vn <= till_name)]
    )
    version = None
    _logger.info(f"Running Upgrades: {upgrades}")
    with self as db:
      with db.cursor() as crs:
        if not current_v:
          assert meta_schema is not None and meta_seed is not None
          with open(meta_schema, "r") as mscF:
            ddl = mscF.read()
            crs.executescript(ddl)
          with open(meta_seed, "r") as msF:
              dml = msF.read()
              _logger.debug(f"Executing {meta_seed}")
              crs.executescript(dml)
        for upgrade in upgrades:
          regex = re.search(r"\d+.sql", upgrade)
          if regex:
            v = int(regex.group()[:-4])
            if upgrade in schemas:
              with open(schemas[upgrade], "r") as schF:
                  ddl = schF.read()
                  _logger.debug(f"Executing Schema {schemas[upgrade].name}")
                  crs.executescript(ddl)
            if upgrade in seeds:
              with open(seeds[upgrade], "r") as seed_file:
                dml = seed_file.read()
                _logger.debug(f"Executing Schema {seed_file.name}")
                crs.executescript(dml)
              version = self._update_version_in_cursor(crs, v)

    return version
