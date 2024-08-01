import logging

from pyway.migrate import Migrate  # type: ignore
from pyway.settings import ConfigFile  # type: ignore

from salduba.common.configuration import DbConfig

_logger = logging.getLogger(__name__)


def init_db(configuration: DbConfig) -> None:
  config = ConfigFile()
  config.database_type = 'sqlite'
  config.database_name = str(configuration.storage_path.absolute())
  config.database_table = 'pyway_info'
  config.database_migration_dir = configuration.migration_path

  _logger.info(Migrate(config).run())
