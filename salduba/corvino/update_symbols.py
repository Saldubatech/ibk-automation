from typing import Optional
import datetime
from threading import Timer
import logging

# from salduba.ib_tws_proxy.util import LocalLogger
from salduba.ib_tws_proxy.configuration import Configuration
from salduba.ib_tws_proxy.backing_db.db import TradingDB
from salduba.ib_tws_proxy.conid_updater.updater import SymbolUpdater
from salduba.corvino.model import Movement

_logger = logging.getLogger(__name__)


def update_symbols(config_file_name: str = 'configuration.yml', 
                   probeSize: Optional[int] = None,
                   live: bool = True) -> None:
  app_name = 'update-conid-db'
  logging.info("Starting at %s", datetime.datetime.now())

  config = Configuration(app_name, config_file_name)
  logging.info(f"Setting Log Level to {config.logLevel}")
  _logger.setLevel(config.logLevel)

  movements = Movement.fromFile(config.movements_path, config.batch)

  _logger.info(f"Will Find {len(movements)} symbols from {config.movements_path} with batch: {config.batch}")
  _logger.info(f"Server is: {config.host}:{config.port} and Client: {config.clientId}")

  db = TradingDB(config.dbConfig)
  db.configure()
  if live:
    try:
      probe: list[str] = list(movements.keys())[0:probeSize] if probeSize else list(movements.keys())
      proxy = SymbolUpdater(db,
                            probe,
                            config.unconfirmed_csv_path,
                            config.not_found_symbols_csv_path,
                            searchDelay=config.search_delay,
                            logLevel=config.logLevel)
      try:
        # This is just to test a few
        proxy.connect(config.host, port=config.port, clientId=config.clientId)  # type: ignore
        _logger.info(
          "serverVersion: %s connectionTime: %s" %
          (proxy.serverVersion(), proxy.twsConnectionTime()))
        # Processing will last 1.1 secs per item max (safeguard)
        interval = int(len(proxy.refresh_required)*1.2)*config.search_delay+5  # to allow for connection time.
        _logger.info(f"Will run for {interval} seconds")
        Timer(interval, proxy.stop, args=["Time Exhausted"]).start()
        # This starts the listener
        proxy.run()

      except Exception as exc:
        _logger.fatal(f"Found an Exception: {exc}")
      finally:
        _logger.info("Finalizing at: %s", datetime.datetime.now())
    except Exception as exc:
      _logger.fatal(f"Exception while initializing SymbolUpdater: {exc}")
    finally:
      pass
  else:
    _logger.info(f"Non Live Execution: ({config_file_name}, {probeSize})")
    _logger.info(f"With Configuration: {config}")
