import logging
import os
import re
import sqlite3 as sql
import traceback
from types import TracebackType
from typing import Any, Callable, Generic, Iterable, Optional, Type, TypeVar

import pandas as pd

from salduba.ib_tws_proxy.backing_db.record import Record, RecordMeta

_logger = logging.getLogger(__name__)


class DbConfig:
    def __init__(self, cfg_dict: dict[str, str]):
        self.storage = cfg_dict["path"]
        self.schema_dir = cfg_dict["schemas"]
        self.seed_dir = cfg_dict["seed_data"]
        self.expected_version = int(cfg_dict["expected_version"])
        self.target_version = int(cfg_dict["target_version"])
        self.version_date = cfg_dict["version_date"]
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
    def __init__(self, config: DbConfig) -> None:
        self.config = config
        self.conn: Optional[sql.Connection] = None
        self.connection_depth = 0

    def connect(self) -> "TradingDB":
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
        dbV = self.version()
        if dbV:
            _logger.debug(f"VERSION AT: {dbV.version}")
            current_v = dbV.version
        else:
            _logger.info("No Db Version Found, assuming 0")
            current_v = 0
        if current_v == self.config.target_version:
            _logger.info(f"Db Version already at target: {self.config.target_version}")
        else:
            _logger.info(f"Upgrading Db Version from {current_v} to {self.config.target_version}")
            rs = self.ensure_version(self.config.target_version)
        return rs

    def version(self, v: Optional[int] = None) -> Optional[DbVersion]:
        with self as db:
            with db.cursor() as crs:
                tables = crs.execute("SELECT name From sqlite_master where name = 'db_info'").fetchone()
                if not tables:
                    rs: Optional[tuple[int, int, int, bool]] = None
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
        with self as db:
            with db.cursor() as _:
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
        _logger.debug(f"Upgrading with target: {v}")
        inserter = """
      insert into db_info (version, version_time, at, current)
      values (?, unixepoch(?, 'utc'), CURRENT_TIMESTAMP, TRUE);
      """
        _logger.debug(f"New Version Insertion: {inserter}")
        insert_params = [v, self.config.version_date]
        _logger.debug(f"\tWith params: {insert_params}")
        cursor.execute(inserter, insert_params)
        obsoleter = """
      update db_info set current = FALSE where version <> ?;
      """
        _logger.debug(f"Obsoleting with {obsoleter}")
        obsolete_params = [v]
        _logger.debug(f"\tWith params {obsolete_params}")
        cursor.execute(obsoleter, obsolete_params)
        return self.version()

    def _upgrade_from(self, current_v: Optional[DbVersion], to: Optional[int] = None) -> Optional[DbVersion]:
        schemas: list[str] = os.listdir(self.config.schema_dir)
        _logger.debug(f"Schemas: {schemas}")
        seeds: list[str] = os.listdir(self.config.seed_dir)
        _logger.debug(f"Seeds: {seeds}")
        schemas.remove("meta.sql")
        seeds.remove("meta.sql")
        unified = sorted(set(schemas + seeds))
        current_name = "v{:04d}.sql".format(current_v.version) if current_v else "a"
        till_name = "v{:04d}.sql".format(to) if to else "z"
        upgrades = sorted(
            [vn for vn in unified if (not current_name or vn > current_name) and (not till_name or vn <= till_name)]
        )
        version = None
        _logger.info(f"Running Upgrades: {upgrades}")
        with self as db:
            with db.cursor() as crs:
                if not current_v:
                    with open(f"{self.config.schema_dir}/meta.sql", "r") as meta_schema:
                        sch = meta_schema.read()
                        crs.executescript(sch)
                    with open(f"{self.config.seed_dir}/meta.sql", "r") as meta_seed:
                        seed = meta_seed.read()
                        _logger.debug(f"Executing {meta_seed.name}")
                        crs.executescript(seed)
                for upgrade in upgrades:
                    regex = re.search(r"\d+.sql", upgrade)
                    if regex:
                        v = int(regex.group()[:-4])
                        if upgrade in schemas:
                            with open(f"{self.config.schema_dir}/{upgrade}", "r") as schema:
                                sch = schema.read()
                                _logger.debug(f"Executing Schema {schema.name}")
                                crs.executescript(sch)
                        if upgrade in seeds:
                            with open(f"{self.config.seed_dir}/{upgrade}", "r") as seed_file:
                                seed = seed_file.read()
                                _logger.debug(f"Executing Schema {seed_file.name}")
                                crs.executescript(seed)
                        version = self._update_version_in_cursor(crs, v)
        return version


M = TypeVar("M", bound=RecordMeta)
R = TypeVar("R", bound=Record)


class Repo(Generic[M, R]):
    def __init__(
        self,
        db: TradingDB,
        record: RecordMeta,
        hydrator: Callable[[Iterable[Any]], R],
    ) -> None:
        self.db = db
        self.record = record
        self.hydrator = hydrator

    def insert(self, records: list[R]) -> None:
        with self.db as db:
            with db.cursor() as crs:
                crs.executemany(self.record.value_inserter, [r.values() for r in records])

    def select_raw(self, *conditions: str) -> list[tuple[Any]]:
        results = []
        with self.db as db:
            with db.cursor() as crs:
                results = crs.execute(self.record.selector + " where " + " and ".join(conditions) + ";").fetchall()
        return results

    def select(self, *conditions: str) -> list[R]:
        results = self.select_raw(*conditions)
        return [self.hydrator(r) for r in results]

    def selectAsDataFrame(self, *conditions: str) -> pd.DataFrame:
        results = self.select_raw(*conditions)
        return pd.DataFrame(results, columns=self.record.all_fields)
