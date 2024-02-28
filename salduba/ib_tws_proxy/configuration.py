import logging
import datetime
from pathlib import Path
import copy
import yaml
import mergedeep  # type: ignore

from salduba.ib_tws_proxy.backing_db.db import DbConfig


class Configuration:
  default = {
    "logging": {
      "level": "INFO"
    },
    "tws_server": {
      "host": "127.0.0.1",
      "port": "7497"
    },
    "client": {
      "id": "0"
    },
    "inputs": {
      "movements_path": "data/movements.csv",
    }
  }
  default['inputs']['batch'] = f"{Path(default['inputs']['movements_path']).stem}::{datetime.datetime.now()}"

  def __init__(self, app_id: str, config_path: str = 'configuration.yml') -> None:
    self.app_id = app_id
    self.config = copy.deepcopy(Configuration.default)
    with open(config_path, 'r') as config_file:
      try:
        loaded_config = yaml.safe_load(config_file)
        mergedeep.merge(self.config, loaded_config)  # type: ignore
      except yaml.YAMLError as exc:
        logging.warn(f"Could not read configuration file: '{config_path}' because of {exc}, using default")

    self.host = self.config['tws_server']['host']

    port = self.config['tws_server']['port']
    if isinstance(port, int):
      self.port = port
    elif port.isdigit():
      self.port = int(port)
    else:
      self.port = int(Configuration.default['tws_server']['port'])

    clId = self.config['client'][self.app_id]
    if isinstance(clId, int):
      self.clientId = clId
    elif clId.isdigit():
      self.clientId = int(clId)
    else:
      raise Exception("App Id not found in configuration")

    self.logLevel: int = logging.getLevelNamesMapping()[self.config['logging']['level']]
    self.movements_path = self.config['inputs']['movements_path']
    self.batch = self.config['inputs']['batch']

    self.dbConfig: DbConfig = DbConfig(self.config['trading_db'])
