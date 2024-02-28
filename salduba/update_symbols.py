from typing import Optional
import datetime
from threading import Timer
import logging

from salduba.ib_tws_proxy.util import LocalLogger
from salduba.ib_tws_proxy.configuration import Configuration
from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.conid_updater.updater import SymbolUpdater
from salduba.corvino.model import Movement


def update_symbols(config_file_name: str = 'configuration.yml', probeSize: Optional[int] = None, live: bool = True) -> None:
  localLogger = LocalLogger(level=logging.INFO)
  app_name = 'update-conid-db'
  logging.info("Starting at %s", datetime.datetime.now())

  config = Configuration(app_name, config_file_name)
  localLogger.setLevel(level=config.logLevel)

  movements = Movement.fromFile(config.movements_path, config.batch)

  logging.info(f"Will Find {len(movements)} symbols from {config.movements_path} with batch: {config.batch}")
  logging.info(f"Server is: {config.host}:{config.port} and Client: {config.clientId}")

  if live:
    try:
      db = TradingDB(config.dbConfig)
      probe: list[str] = list(movements.keys())[0:probeSize] if probeSize else list(movements.keys())
      proxy = SymbolUpdater(db, probe)
      # This is just to test a few
      proxy.connect(config.host, port=config.port, clientId=config.clientId)  # type: ignore
      print(
        "serverVersion: %s connectionTime: %s" %
        (proxy.serverVersion(), proxy.twsConnectionTime()))
      # Processing will last 1.1 secs per item max (safeguard)
      interval = int(len(probe)*1.1)+5  # to allow for connection time.
      Timer(interval, proxy.stop, args=["Time Exhausted"]).start()
      # This starts the listener
      proxy.run()
    except Exception as exc:
      logging.fatal(f"Found an Exception: {exc}")
      raise
    finally:
      logging.info("Finalizing at: %s", datetime.datetime.now())


if __name__ == "__main__":
  print('Executing')
  update_symbols(10, False)
