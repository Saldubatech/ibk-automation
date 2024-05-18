import copy
import datetime
import logging
from pathlib import Path

import mergedeep  # type: ignore
import yaml

from salduba.ib_tws_proxy.backing_db.db import DbConfig


class Configuration:
    default = {
        "logging": {"level": "INFO"},
        "tws_server": {
            "host": "127.0.0.1",
            "port": "7497",
            "search-delay": "0.5",
        },
        "client": {"id": "0"},
        "inputs": {
            "movements_path": "data/movements.csv",
        },
        "outputs": {
            "unconfirmed_csv_path": "data/default_unconfirmed_contracts.csv",
            "not_found_symbols_csv_path": "data/default_symbols_not_found.csv",
        },
    }
    default["inputs"]["batch"] = f"{Path(default['inputs']['movements_path']).stem}::{datetime.datetime.now()}"

    def __init__(self, app_id: str, config_path: str = "configuration.yml") -> None:
        self.app_id = app_id
        self.config = copy.deepcopy(Configuration.default)
        with open(config_path, "r") as config_file:
            try:
                loaded_config = yaml.safe_load(config_file)
                mergedeep.merge(self.config, loaded_config)
            except yaml.YAMLError as exc:
                logging.warn(f"Could not read configuration file: '{config_path}' because of {exc}, using default")

        self.host: str = self.config["tws_server"]["host"]

        port = self.config["tws_server"]["port"]
        if isinstance(port, int):
            self.port: int = port
        elif port.isdigit():
            self.port = int(port)
        else:
            self.port = int(Configuration.default["tws_server"]["port"])

        clId = self.config["client"][self.app_id]
        if isinstance(clId, int):
            self.clientId: int = clId
        elif clId.isdigit():
            self.clientId = int(clId)
        else:
            raise Exception("App Id not found in configuration")

        self.logLevel: int = logging.getLevelNamesMapping()[self.config["logging"]["level"]]
        self.movements_path = self.config["inputs"]["movements_path"]
        self.batch = self.config["inputs"]["batch"]
        self.not_found_symbols_csv_path = self.config["outputs"]["not_found_symbols_csv_path"]
        self.dbConfig: DbConfig = DbConfig(self.config["trading_db"])
        # self.updater_config = UpdaterConfig(self.config, logLevel=self.logLevel)
        self.unconfirmed_csv_path = self.config["outputs"]["unconfirmed_csv_path"]
        self.search_delay = float(self.config["tws_server"]["search-delay"])

    def __repr__(self) -> str:
        return str(self.__dict__)
