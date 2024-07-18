import datetime
import logging
import shutil
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from importlib import resources as lib_res
from importlib.abc import Traversable
from pathlib import Path
from typing import Any, Iterator, Optional

import click
import yaml
from platformdirs import PlatformDirs, PlatformDirsABC

_logger = logging.getLogger(__name__)


@dataclass
class Meta:
  app_id: str = 'cervino'
  home: Path = field(default_factory=Path.home)
  cwd: Path = field(default_factory=Path.cwd)
  resources_path: Traversable = field(default_factory=(lambda : lib_res.files('salduba.corvino.resources')))
  config_file_name: str = f'{app_id}_config.yml'

  override_config_path: Optional[Path] = None

  @property
  def config_dir_path(self) -> Path:
    return self.override_config_path if self.override_config_path else Path(self.home, f".{self.app_id}")

  @property
  def default_config_file_context(self) -> AbstractContextManager[Path]:
    return lib_res.as_file(self.resources_path.joinpath(self.config_file_name))

  @staticmethod
  def config_path(ctx: click.Context, param: click.Option | click.Parameter, path: Optional[Any]) -> str:
    assert isinstance(path, str) or path is None
    return path if path else str(defaultMeta.config_file_path)

  log_file_name = "logging.yml"

  @property
  def default_log_config_file_context(self) -> AbstractContextManager[Path]:
    return lib_res.as_file(self.resources_path.joinpath(self.log_file_name))

  cervino_key: str = "cervino"
  input_key = "input"
  output_key = "output"
  db_key = "db"
  tws_key = "tws"

  @property
  def platform(self) -> PlatformDirsABC:
    return PlatformDirs(self.app_id)

  @property
  def log_config_path(self) -> Path:
    return self.resolve_configuration_file(self.log_file_name, self.default_log_config_file_context)

  @property
  def config_file_path(self) -> Path:
    return self.resolve_configuration_file(self.config_file_name, self.default_config_file_context)

  def resolve_configuration_file(
      self,
      file_name: str,
      default_contents: AbstractContextManager[Path]) -> Path:
    config_dir_candidates: list[Path] = [
          self.config_dir_path,
          self.home,
          Path(self.platform.user_config_dir),
          Path(self.platform.user_documents_dir),
          Path(self.platform.user_desktop_dir),
          self.cwd
        ]
    existing_config_dirs: list[Path] = [cd for cd in config_dir_candidates if cd.is_dir()]
    config_file_candidates = [
      cf for cf in [cd.joinpath(file_name) for cd in existing_config_dirs] if cf.is_file()]
    if config_file_candidates:
      file_path = config_file_candidates[0]
    else:
      config_dir = existing_config_dirs[0]
      if config_dir == self.home:
        self.config_dir_path.mkdir()
        config_dir = self.config_dir_path
      file_path = config_dir.joinpath(file_name)
    if not file_path.exists():
      if not file_path.parent.exists():
        file_path.parent.mkdir()
      with default_contents as default_file:
        shutil.copyfile(default_file, file_path)
    return file_path

  def resolve_storage_file(self, storage_name: str, override_dir: Optional[str] = None) -> Path:
    if override_dir:
      storage_path = Path(override_dir).joinpath(storage_name)
    else:
      dir_candidates = [
        self.config_dir_path,
        self.home,
        self.platform.user_data_path,
        self.platform.user_documents_path,
        self.platform.user_desktop_path,
        self.cwd
      ]
      in_existing_dirs = [dp.joinpath(storage_name) for dp in dir_candidates if dp.is_dir()]
      path_candidates = [candidate for candidate in in_existing_dirs if candidate.exists()]
      if path_candidates:
        storage_path = path_candidates[0]
      else:
        if str(in_existing_dirs[0].parent) == str(self.home):
          storage_path = self.config_dir_path.joinpath(storage_name)
        else:
          storage_path = in_existing_dirs[0]

    if not storage_path.parent.exists():
      storage_path.parent.mkdir()
    if not storage_path.is_file():
      storage_path.touch()
    return storage_path

  @property
  def resolve_config(self) -> 'Cfg':
    config_file = self.config_file_path
    with open(config_file, 'r') as cf:
      dictCfg = yaml.safe_load(cf.read())
      rs = Cfg.configure(self, dictCfg)
    return rs


defaultMeta = Meta()


@dataclass
class TwsConfig:
  port: int = 7497
  host: str = 'localhost'

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'TwsConfig':
    d: dict[str, Any] = {}
    if 'port' in values:
      d['port'] = int(values['port'])
    if 'host' in values:
      d['host'] = values['host']
    return TwsConfig(**d)


@dataclass
class InputConfig:
  input_dir: Path = Path.cwd()
  file_prefix: str = "movements"
  file_name: str = file_prefix + ".csv"
  sheet_name: str = "Movements"

  @staticmethod
  def input_path(ctx: click.Context, param: click.Option | click.Parameter, value: Any) -> str:
    assert isinstance(value, str) or value is None
    return str(Path(value) if value else Defaults.input.input_dir)

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'InputConfig':
    d: dict[str, Any] = {}
    if 'input_dir' in values:
      d['input_dir'] = Path(values['input_dir'])
    if 'file_prefix' in values:
      d['file_prefix'] = values['file_prefix']
    if 'file_name' in values:
      d['file_name'] = values['file_name']
    if 'sheet_name' in values:
      d['sheet_name'] = values['sheet_name']
    return InputConfig(**d)


@dataclass
class OutputConfig:
  output_dir: Path = Path.cwd()
  file_prefix: str = "cervino_command_output"
  file_name: str = file_prefix + '.xlsx'
  inputs_sheet: str = "inputs"
  known_sheet: str = "known"
  updated_sheet: str = "updated"
  missing_sheet: str = "missing"
  movement_sheet: str = "movement"
  error_sheet: str = "errors"

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'OutputConfig':
    d: dict[str, Any] = {}
    if 'output_dir' in values:
      d['output_dir'] = Path(values['output_dir'])
    if 'file_prefix' in values:
      d['file_prefix'] = values['file_prefix']
    if 'file_name' in values:
      d['file_name'] = values['file_name']
    if 'inputs_sheet' in values:
      d['inputs_sheet'] = values['inputs_sheet']
    if 'known_sheet' in values:
      d['known_sheet'] = values['known_sheet']
    if 'updated_sheet' in values:
      d['updated_sheet'] = values['updated_sheet']
    if 'missing_sheet' in values:
      d['missing_sheet'] = values['missing_sheet']
    if 'movement_sheet' in values:
      d['movement_sheet'] = values['movement_sheet']
    if 'error_sheet' in values:
      d['error_sheet'] = values['error_sheet']
    return OutputConfig(**d)


@dataclass
class CervinoConfig:
  data_dir: Path
  meta: Meta = field(default_factory=(lambda : defaultMeta))
  batch_prefix: str = 'order_batch'

  @staticmethod
  def batch_name(ctx: click.Context, param: click.Option | click.Parameter, value: Any) -> str:
    assert isinstance(value, str) or value is None
    nowT = datetime.datetime.now()
    return value if value else f"{Defaults.cervino.batch_prefix}_{nowT.strftime('%Y%m%d%H%M%S')}"

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'CervinoConfig':
    d: dict[str, Any] = {'meta': meta}
    if 'data_dir' in values:
      d['data_dir'] = Path(values['data_dir'])
    else:
      d['data_dir'] = meta.home.joinpath(f".{meta.app_id}")
    if 'batch_prefix' in values:
      d['batch_prefix'] = values['batch_prefix']
    return CervinoConfig(**d)


@dataclass
class DbConfig:
  meta: Meta = field(default_factory=(lambda : defaultMeta))
  storage_name: str = 'cervino.db'
  min_required_version: Optional[int] = None
  max_required_version: Optional[int] = None
  version_date: str = "2024-02-01 00:00:00.000"
  @property
  def _db_schemas_path(self) -> Traversable: return lib_res.files('salduba.ib_tws_proxy.backing_db.schema')
  @property
  def db_schemata(self) -> Iterator[Traversable]: return self._db_schemas_path.iterdir()
  @property
  def _db_seed_path(self) -> Traversable: return lib_res.files('salduba.ib_tws_proxy.backing_db.seed-data')
  @property
  def db_seeds(self) -> Iterator[Traversable]: return self._db_seed_path.iterdir()
  @property
  def storage_path(self) -> Path: return self.meta.resolve_storage_file(self.storage_name)

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'DbConfig':
    d: dict[str, Any] = {'meta': meta}
    if 'storage_name' in values:
      d['storage_name'] = values['storage_name']
    if 'min_required_version' in values and values['min_required_version']:
      d['min_required_version'] = int(values['min_required_version'])
    if 'max_required_version' in values and values['max_required_version']:
      d['max_required_version'] = int(values['max_required_version'])
    if 'version_date' in values:
      d['version_date'] = values['version_date']
    return DbConfig(**d)


@dataclass
class Cfg:
  meta: Meta = field(default_factory=(lambda : defaultMeta))
  cervino: CervinoConfig = field(
    default_factory=(lambda : CervinoConfig(data_dir=Path.home().joinpath(f".{defaultMeta.app_id}"))))
  input: InputConfig = field(default_factory=(lambda : InputConfig()))
  output: OutputConfig = field(default_factory=(lambda : OutputConfig()))
  db: DbConfig = field(default_factory=(lambda : DbConfig()))
  tws: TwsConfig = field(default_factory=(lambda : TwsConfig()))

  @staticmethod
  def configure(meta: Meta, values: dict[str, Any]) -> 'Cfg':
    d: dict[str, Any] = {'meta': meta}
    if meta.cervino_key in values:
      d[meta.cervino_key] = CervinoConfig.configure(meta, values[meta.cervino_key])
    if meta.input_key in values:
      d[meta.input_key] = InputConfig.configure(meta, values[meta.input_key])
    if meta.output_key in values:
      d[meta.output_key] = OutputConfig.configure(meta, values[meta.output_key])
    if meta.db_key in values:
      d[meta.db_key] = DbConfig.configure(meta, values[meta.db_key])
    if meta.tws_key in values:
      d[meta.tws_key] = TwsConfig.configure(meta, values[meta.tws_key])
    return Cfg(**d)


Defaults = Cfg()
