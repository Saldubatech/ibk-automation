import datetime
import logging
import os
from pathlib import Path
from typing import List, Optional

import click

from salduba.util.sys.paths import module_path

_logger = logging.getLogger(__name__)


class Configuration:
  corvino_dir_name = '.corvino'
  default_db_name = 'corvino.db'
  default_missing_output = Path(os.getcwd()).joinpath('missing-contracts.csv')
  default_movement_input = Path(os.getcwd()).joinpath('movements.csv')
  default_movements_sheet = 'Movements'
  default_tws_host = 'localhost'
  default_tws_port = 7497
  configuration_module_path: List[str] = module_path(__name__)
  default_log_config_file = 'corvino_logging.yaml'
  default_batch_prefix = 'order_batch'

  @staticmethod
  def _corvino_dir() -> Path:
    user_home = os.getenv('HOME')
    if not user_home:
      msg1 = "The HOME environment variable is not defined"
      msg2 = "Ensure that the HOME environment variable is set to a valid diretory (folder)"
      _logger.error(msg1 + '\n\t' + msg2)
      raise click.FileError(msg1, msg2)
    else:
      path = Path(user_home).joinpath(Configuration.corvino_dir_name)
      if not path.exists():
        os.mkdir(path)
      elif not path.is_dir():
        msg = f"The path {path} exists but it is not a directory"
        _logger.error(msg)
        raise click.FileError(
          str(path),
          msg)
      return path

  @staticmethod
  def db_path(ctx: click.Context, param: click.Option, db_path: Optional[str]) -> str:
    return str(
      Path(db_path) if db_path else Configuration._corvino_dir().joinpath(Configuration.default_db_name)
    )

  @staticmethod
  def output_path(ctx: click.Context, param: click.Option, missing_contracts_output: Optional[str]) -> str:
    return str(Path(missing_contracts_output) if missing_contracts_output else Configuration.default_missing_output)

  @staticmethod
  def input_path(ctx: click.Context, param: click.Option, value: Optional[str]) -> str:
    return str(Path(value) if value else Configuration.default_movement_input)

  @staticmethod
  def input_sheet(ctx: click.Context, param: click.Option, value: Optional[str]) -> str:
    return value if value else Configuration.default_movements_sheet

  @staticmethod
  def batch_name(ctx: click.Context, param: click.Option, value: Optional[str]) -> str:
    nowT = datetime.datetime.now()
    return value if value else f"{Configuration.default_batch_prefix}_{nowT.strftime('%Y%m%d%H%M%S')}"
