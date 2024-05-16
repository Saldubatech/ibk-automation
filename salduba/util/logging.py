from typing import Optional
import logging
import logging.config
import yaml

from salduba.util.files import resolveFile


_default_log_config_file = resolveFile('logging.yaml')


def init_logging(config_file: Optional[str] = _default_log_config_file):
  if config_file:
    with open(config_file) as f:
      config = yaml.safe_load(f)
      logging.config.dictConfig(config)

