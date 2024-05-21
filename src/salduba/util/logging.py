import logging
import logging.config
import os
from pathlib import Path
from typing import List, Optional

import yaml

from salduba.util.files import resolveFileInPath
from salduba.util.sys.paths import module_path


def find_log_file(user_config_sub_dir: str, package_hierarchy: List[str], log_file_name: str) -> Path:
    # First if relative to CWD
    path: Optional[Path] = Path(log_file_name)
    if path and path.exists() and path.is_file():
        # First in the current directory
        return path
    # the in the home directory under `.corvino` in the User's home
    home = os.getenv('HOME')
    if home:
        path = Path(home, user_config_sub_dir, log_file_name)
        if path.exists() and path.is_file():
            return path
    # Finally in the path from most specific to less specific
    candidates: List[List[str]] = [
                                    package_hierarchy[0:i] + [log_file_name]
                                    for i in range(0, len(package_hierarchy) + 1)
                                  ][::-1]

    for candidate in candidates:
        path = resolveFileInPath(str(Path(*candidate)))
        if path:
            return path
    # This is guaranteed to exist by construction of the salduba.corvino package.
    this_package_path = Path(*module_path(__name__))
    return this_package_path.joinpath(log_file_name)


class DefaultConfiguration:
  user_sub_dir = '.corvino'
  log_file_name = 'logging.yaml'
  log_file_path = find_log_file(user_sub_dir, module_path(__name__), log_file_name)


def init_logging(config_file: Path = DefaultConfiguration.log_file_path) -> None:
  with open(config_file) as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)
