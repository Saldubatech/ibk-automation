import logging
import tempfile
from typing import Optional, Tuple

import click
import pandas as pd

from salduba.corvino.commands.configuration import Configuration
from salduba.corvino.parse_input import InputParser
from salduba.corvino.persistence.movement_record import MovementRepo
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.backing_db.db import DbConfig, TradingDB
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRepo, DeltaNeutralContractRepo
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRepo, OrderStatusRepo, SoftDollarTierRepo
from salduba.util.files import resolveDir
from salduba.util.logging import find_log_file, init_logging
from salduba.util.sys.paths import module_path

_log_file = find_log_file(
  Configuration.corvino_dir_name,
  module_path(__name__),
  Configuration.default_log_config_file)

init_logging(_log_file)

_logger = logging.getLogger(__name__)


def _all_repos(
    dbFilePath: Optional[str]
) -> Tuple[TradingDB, DeltaNeutralContractRepo, ContractRepo, OrderRepo, MovementRepo]:
  if dbFilePath:
    dbFile = dbFilePath
  else:
    tmp_file = tempfile.NamedTemporaryFile()
    tmp_file.close()
    dbFile = tmp_file.name
  schemata = resolveDir("salduba/ib_tws_proxy/backing_db/schema")
  seed_data = resolveDir("salduba/ib_tws_proxy/backing_db/seed-data")
  if not schemata or not seed_data:
    raise Exception("Schema or Seed Data directories not found")
  db_config = DbConfig(
    {
      "path": dbFile,
      "schemas": schemata,
      "seed_data": seed_data,
      "expected_version": "0",
      "target_version": "1",
      "version_date": "2024-02-01 00:00:00.000",
    }
  )
  db = TradingDB(db_config)
  db.configure()
  dnc_repo = DeltaNeutralContractRepo(db)
  contract_repo = ContractRepo(db, dnc_repo)
  orderStRepo = OrderStatusRepo(db)
  sdTRepo = SoftDollarTierRepo(db)
  order_repo = OrderRepo(db, sdTRepo, orderStRepo)
  movement_repo = MovementRepo(db, contract_repo, order_repo)
  return db, dnc_repo, contract_repo, order_repo, movement_repo


def build_app(dbFilePath: Optional[str]) -> CorvinoApp:
  _, dnc_repo, contract_repo, order_repo, movement_repo = _all_repos(dbFilePath)
  app = CorvinoApp(
    contract_repo,
    dnc_repo,
    movement_repo,
    order_repo,
    appFamily=1000,
    host=Configuration.default_tws_host,
    port=Configuration.default_tws_port)
  return app


def require_csv_or_xlsx(param: click.Option, value: str) -> Optional[str]:
  parts = value.split('.')
  if len(parts) < 2:
    raise click.BadParameter(f"{param.name} must be a *.csv or *.xlsx file")
  elif parts[-1] == 'xlsx' or parts[-1] == 'csv':
    return value
  else:
    raise click.BadParameter(f"{param.name} must be a *.csv or *.xlsx file")


@click.group()
@click.option(
  "--database", "-db",
  type=str,
  required=False,
  help="Path to the database to use",
  callback=Configuration.db_path
)
@click.option(
  "--missing-output",
  type=str,
  required=False,
  help="Path to the output for missing contracts, it must be a *.csv file",
  callback=Configuration.output_path
)
@click.option(
  "--movement-input",
  type=str,
  required=False,
  help="Path to the input file of movements, it must be a *.csv file",
  callback=Configuration.input_path
)
@click.option(
  "--movement-sheet",
  type=str,
  required=False,
  default='Movements',
  help="If the input is a xlsx file with more than one sheet, the name of the sheet with the Movements",
  callback=Configuration.input_sheet
)
@click.pass_context
def cli(
    ctx: click.Context,
    database: str,
    missing_output: str,
    movement_input: str,
    movement_sheet: str
    ) -> None:
  ctx.ensure_object(dict)
  ctx.obj['db_path'] = database
  ctx.obj['missing_output'] = missing_output
  ctx.obj['movement_input'] = movement_input
  ctx.obj['input_type'] = movement_input.split('.')[-1]
  ctx.obj['movement_sheet'] = movement_sheet
  ctx.obj['app'] = build_app(database)


def read_from_input(input_type: str, input_file: str, sheet_name: str) -> pd.DataFrame:
  try:
    if input_type == 'csv':
      df = InputParser.read_csv(input_file)
    elif input_type == 'xlsx':
      df = InputParser.read_excel(input_file, sheet=sheet_name)
    else:
      raise click.BadParameter(f"Invalid input type: {input_type}")
  except (ValueError, FileNotFoundError) as error_exc:
    msg = f"Error reading input file: {input_file}:\n\t{error_exc}.\n\tSee Additional information in the logs"
    _logger.critical(msg, exc_info=error_exc, stack_info=True)
    raise click.FileError(input_file, msg)
  if df is None:
    msg = f"Invalid input file: {input_file}"
    _logger.warning(msg)
    raise click.BadParameter(msg)
  elif df.empty:
    msg = f"No data in input file: {input_file}"
    _logger.warning(msg)
    raise click.BadParameter(msg)
  else:
    return df


@cli.command()
@click.argument(
  "input-movements-file",
  required=True,
  type=click.Path(exists=True),
  callback=Configuration.input_path
)
@click.pass_context
def verify_contracts(ctx: click.Context, input_movements_file: str) -> None:
  app: CorvinoApp = ctx.obj['app']

  missing_output_file: str = ctx.obj['missing_output']
  info_msg = f"Verifying Contracts from {input_movements_file}, missing contracts will be written to: {missing_output_file}"
  debug_msg = f"Using Database: {ctx.obj['db_path']}"
  _logger.info(info_msg)
  _logger.debug(debug_msg)
  click.echo(info_msg)
  df = read_from_input(ctx.obj['input_type'], input_movements_file, ctx.obj['movement_sheet'])
  result = app.verify_contracts_for_dataframe(df, missing_output_file)
  if result is not None and len(result) > 0:
    msg = f"Missing Contracts: {len(result)}"
    click.echo(msg)
    _logger.info(msg)


@cli.command()
@click.pass_context
@click.argument(
  "input-movements-file",
  required=False,
  type=click.Path(exists=True),
  callback=Configuration.input_path
)
def lookup_contracts(ctx: click.Context, input_movements_file: str) -> pd.DataFrame:
  return _do_lookup_contracts(ctx, input_movements_file)


def _do_lookup_contracts(ctx: click.Context, input_movements_file: str) -> pd.DataFrame:
  app: CorvinoApp = ctx.obj['app']
  missing_output_file: str = ctx.obj['missing_output']
  info_msg = f"Looking up Contracts from {input_movements_file}, missing contracts will be written to: {missing_output_file}"
  debug_msg = f"Using Database: {ctx.obj['db_path']}"
  _logger.info(info_msg)
  _logger.debug(debug_msg)
  click.echo(info_msg)
  df = read_from_input(ctx.obj['input_type'], input_movements_file, ctx.obj['movement_sheet'])
  result = app.lookup_contracts(df, missing_output_file)
  if result is not None and len(result) > 0:
    msg = f"Cannot resolve some Contracts[{len(result)}]. See {missing_output_file} for details"
    click.echo(msg)
    _logger.error(msg)
    raise click.ClickException(msg)
  else:
    msg = "All Contracts resolved"
    click.echo(msg)
    _logger.info(msg)
  return df


@cli.command()
@click.option(
  "--batch",
  type=str,
  required=False,
  help="The name of the batch to use for these orders",
  callback=Configuration.batch_name
)
@click.argument(
  "input-movements-file",
  required=False,
  type=click.Path(exists=True),
  callback=Configuration.input_path
)
@click.pass_context
def place_orders(ctx: click.Context, batch: str, input_movements_file: str) -> None:
  df = _do_lookup_contracts(ctx, input_movements_file)
  app: CorvinoApp = ctx.obj['app']
  info_msg = f"Placing Orders from {input_movements_file}"
  _logger.info(info_msg)
  click.echo(info_msg)
  msg = app.placeOrders(df, batch, None)
  if "ERRORS" in msg.upper():
    click.echo("Errors while placing Orders. Please look at the log files for information", err=True)
    click.echo(f"Current Active Logs: {[h.name for h in _logger.handlers]}", err=True)
    _logger.error(msg)
    raise click.ClickException(msg)
  else:
    click.echo(msg)
    _logger.info(msg)


if __name__ == "__main__":
  cli(obj={})
