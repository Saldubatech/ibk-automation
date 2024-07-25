import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from salduba.common.configuration import CervinoConfig, Cfg, InputConfig, Meta, defaultMeta
from salduba.common.persistence.alchemy.db import Db, UnitOfWork
from salduba.common.persistence.alchemy.repo import RecordBase
from salduba.common.persistence.pyway.migrating import init_db
from salduba.corvino.io.parse_input import InputParser, InputRow
from salduba.corvino.io.results_out import ResultsBatch
from salduba.corvino.persistence.movement_record import MovementRecordOps
from salduba.corvino.services.app import CorvinoApp
from salduba.ib_tws_proxy.contracts.contract_repo import ContractRecordOps, DeltaNeutralContractOps
from salduba.ib_tws_proxy.orders.OrderRepo import OrderRecordOps
from salduba.util.logging import init_logging

initial_configuration = defaultMeta


with initial_configuration.log_config_path as l_path:
  init_logging(l_path)

_logger = logging.getLogger(__name__)


def build_app(configuration: Cfg) -> CorvinoApp:
  init_logging(configuration.meta.log_config_path)

  init_db(configuration.db)
  db = Db.from_url(
    f"sqlite:///{configuration.db.storage_path.absolute()}",
    echo=configuration.db.echo)

  app = CorvinoApp(
    db=db,
    contract_repo=ContractRecordOps(),
    dnc_repo=DeltaNeutralContractOps(),
    movements_repo=MovementRecordOps(),
    order_repo=OrderRecordOps(),
    appFamily=1000,
    host=configuration.tws.host,
    port=configuration.tws.port)
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
  "--config", "-c",
  type=str,
  required=False,
  help="Path to the configuration file to use",
  callback=Meta.config_path
)
@click.pass_context
def cli(
    ctx: click.Context,
    config: str
    ) -> None:
  config_path = Path(config)
  meta = Meta(override_config_path=config_path.parent)
  cfg = meta.resolve_config
  ctx.ensure_object(dict)
  ctx.obj['config'] = cfg
  ctx.obj['app'] = build_app(cfg)


@cli.command(
  help=click.style("USE FOR DEVELOPMENT ONLY", fg="bright_red") + """\n
    This command will dump the required DB schema for the application
  """
)
@click.pass_context
def dump_ddl(ctx: click.Context) -> None:
  app: CorvinoApp = ctx.obj['app']
  app.db.print_schema(RecordBase.metadata)


@cli.command()
@click.argument(
  "input-movements-file",
  required=True,
  type=click.Path(exists=True),
  callback=InputConfig.input_path
)
@click.pass_context
def verify_contracts(ctx: click.Context, input_movements_file: str) -> None:
  """
  Verify whether the system already has up-to-date information about
  the contracts needed to execute the trades.

  This command works locally and does not need to have TWS running.
  """
  app: CorvinoApp = ctx.obj['app']

  cfg: Cfg = ctx.obj['config']
  cfg.input.file_name = input_movements_file

  info_msg = f"Verifying Contracts from {input_movements_file}"
  debug_msg = f"Using Database: {ctx.obj['config'].db.storage_name}"
  _logger.info(info_msg)
  _logger.debug(debug_msg)
  click.echo(info_msg)

  input_rows = read_input_rows(cfg.input.file_name, cfg.input.sheet_name)
  with app.db.for_work() as uow:
    rs: ResultsBatch = app.verify_contracts_for_input_rows(input_rows, uow)
    if rs.unknown:
      msg = f"Missing Contracts: {len(rs.unknown)}. See {cfg.output.file_name} for details"
      click.echo(msg)
      _logger.info(msg)
    else:
      click.echo("No missing contracts")
    rs.write_xlsx()


@cli.command()
@click.pass_context
@click.argument(
  "input-movements-file",
  required=True,
  type=click.Path(exists=True),
  callback=InputConfig.input_path
)
def lookup_contracts(ctx: click.Context, input_movements_file: str) -> None:
  cfg: Cfg = ctx.obj['config']
  cfg.input.file_name = input_movements_file
  app: CorvinoApp = ctx.obj['app']

  with app.db.for_work() as uow:
    rs = _do_lookup_contracts(ctx.obj['app'], cfg, uow)
    rs.write_xlsx()
    if rs.unknown:
      if rs.errors:
        click.echo(rs.errors)
      _logger.error(rs.message)
      raise click.ClickException(rs.message)
    else:
      _logger.info(rs.message)
      click.echo(rs.message)


@cli.command()
@click.option(
  "--batch",
  type=str,
  required=False,
  help="The name of the batch to use for these orders, default: Date with seconds (Year-Month-Day:Hour:min:secs)",
  callback=CervinoConfig.batch_name
)
@click.option(
  "--execute-trades",
  is_flag=True,
  help=click.style("USE WITH CAUTION!!!!", fg="bright_red") + """\n
    - If the option is provided, the script will execute the trades directly,
    - If not provided, the trades will be uploaded but not executed. The user is then
    expected to execute them if appropriate using the TWS UI itself
  """
)
@click.argument(
  "input-movements-file",
  required=True,
  type=click.Path(exists=True),
  callback=InputConfig.input_path
)
@click.pass_context
def place_orders(ctx: click.Context, batch: str, execute_trades: bool, input_movements_file: str) -> None:
  ctx.obj['config'].input.file_name = input_movements_file
  app: CorvinoApp = ctx.obj['app']
  with app.db.for_work() as uow:
    rs = _do_lookup_contracts(app, ctx.obj['config'], uow)
    if not rs.unknown:
      if execute_trades:
        info_msg = f"Placing Orders from {input_movements_file} "+click.style("WITH DIRECT EXECUTION!!", fg="bright_red")
        confirmation = \
          click.confirm(info_msg + "\n\tDo you want to continue?")
      else:
        info_msg = f"Placing Orders from {input_movements_file} without execution, " +\
          click.style("Please use the TWS UI to execute them", fg="green")
        click.echo(info_msg)
        confirmation = True

      _logger.info(info_msg)

      if confirmation:
        try:
          order_rs = app.place_orders(rs.inputs, uow, batch, execute_trades)
          order_rs.write_xlsx()
          error_keys = [k.upper() for k in rs.errors.keys()]
          if "ERRORS" in error_keys:
            click.echo("Errors while placing Orders. Please look at the log files for information", err=True)
            click.echo(f"Current Active Logs: {[h.name for h in _logger.handlers]}", err=True)
            _logger.error(order_rs.message)
            click.echo("Please see the output file for details")
            raise click.ClickException(order_rs.message)
          else:
            click.echo(order_rs.message)
            _logger.info(order_rs.message)
        except Exception as exc:
          raise click.ClickException(f"An error occurred: {str(exc)}")
      else:
        click.echo("User did not confirm: Abandoning Operation")
        rs.write_xlsx()
    else:
      rs.write_xlsx()


def _do_lookup_contracts(app: CorvinoApp, cfg: Cfg, uow: UnitOfWork) -> ResultsBatch:
  info_msg = f"Looking up Contracts from {cfg.input.file_name}, missing contracts will be written to: {cfg.output.file_name}"
  debug_msg = f"Using Database: {cfg.db.storage_path}"
  _logger.info(info_msg)
  _logger.debug(debug_msg)
  click.echo(info_msg)
  input_rows = read_input_rows(cfg.input.file_name, cfg.input.sheet_name)
  try:
    missing = app.lookup_contracts_for_input_rows(input_rows, uow)
  except Exception as exc:
    raise click.ClickException(f"Unexpected Error occurred: {str(exc)}")
  return ResultsBatch(
    datetime.now(),
    missing.message + " See output file for details"
    if missing.unknown else f"All Contracts resolved, {len(missing.updated)} updated",
    input_rows,
    missing.known,
    missing.updated,
    missing.unknown,
    [],
    missing.errors
  )


def read_input_rows(movements_file: str, sheet: str) -> list[InputRow]:
  try:
    input_rows = InputParser.input_rows_from(movements_file, sheet)
    return input_rows
  except ValueError as vError:
    raise click.ClickException(f"Could not read the file {movements_file}: {str(vError)}")


if __name__ == "__main__":
  cli(obj={})
