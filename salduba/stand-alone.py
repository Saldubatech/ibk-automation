
from threading import Timer
import datetime
import logging

import pandas as pd


from salduba.ib_tws_proxy.configuration import Configuration
from salduba.ib_tws_proxy.util import LocalLogger
from salduba.ib_tws_proxy.standalone import Movement, PlaceOrders


def readMovementsFromPath(movements_path: str, batch: str) -> dict[str, Movement]:
  movementsPD: pd.DataFrame = pd.read_csv(movements_path, index_col='Ticker').sort_values('Ticker').drop('NOTHING', axis=1)  # type: ignore
  movementsPD['Trade'] = movementsPD['Trade'].map(lambda tr : int(tr.replace(',', '')))  # type: ignore
  movementsPD['Id'] = movementsPD['Id'].map(lambda id : int(id))    # type: ignore
  movementsPD['Money'] = movementsPD['Money'].map(lambda m : int(m.replace(',', '')))  # type: ignore
  movementsPD = movementsPD[movementsPD['Trade'] != 0]

  return {
    r['Nombre'].upper() :  Movement(  # type: ignore
      batch,
      r['Id'],   # type: ignore
      r['Nombre'],   # type: ignore
      r['Trade'],   # type: ignore
      r['Currency'],   # type: ignore
      r['Money'],  # type: ignore
      overrideExchange='SMART'
    )
    for idx, r in movementsPD.reset_index().iterrows()  # type: ignore
  }


def main() -> None:
  live = True
  localLogger = LocalLogger(level=logging.INFO)
  config_file_name = 'configuration.yml'
  logging.info("Starting at %s", datetime.datetime.now())

  config = Configuration('stand-alone', config_file_name)
  localLogger.setLevel(level=config.logLevel)

  movements = readMovementsFromPath(config.movements_path, config.batch)

  logging.info(f"Will Process {len(movements)} movements from {config.movements_path} with batch: {config.batch}")
  logging.info(f"Server is: {config.host}:{config.port} and Client: {config.clientId}")

  if live:
    try:
      #  proxy = PlaceOrders(movements=movements, selection=['flatexDEGIRO AG'.upper()])  # type: ignore
      subsetMovements: list[str] = list(movements.keys())[0:10]
      proxy = PlaceOrders(movements=movements, selection=[k.upper() for k in subsetMovements])  # type: ignore
      proxy.connect(config.host, port=config.port, clientId=config.clientId)  # type: ignore
      print(
        "serverVersion: %s connectionTime: %s" %
        (proxy.serverVersion(), proxy.twsConnectionTime()))
      # Processing will last 1.1 secs per movement max (safeguard)
      interval = int(len(subsetMovements)*1.1)+1
      Timer(interval, proxy.stop, args=["Time Exhausted"]).start()
      # This starts the listener
      proxy.run()
    except Exception as exc:
      logging.fatal(f"Found an Exception: {exc}")
      raise
    finally:
      logging.info("Finalizing at: %s", datetime.datetime.now())


if __name__ == "__main__":
    main()
