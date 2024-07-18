import os
from pathlib import Path
from typing import Any, Optional

import yaml
from platformdirs import PlatformDirs, user_config_dir, user_desktop_dir, user_documents_dir


class YamlConfig:
  default_config_file_suffix: str = '_config.yml'

  def __init__(
      self, app_id: str,
      default_config: dict[str, Any] = {},
      config_file_path_override: Optional[str] = None,
      config_file_dir_override: Optional[str] = None) -> None:

    self.default_config_file_name = f"{app_id}{YamlConfig.default_config_file_suffix}"
    self.dirs = PlatformDirs(app_id)

    self.current_directory = Path.cwd()
    self.home = Path.home()

    if config_file_path_override:
      self.config_file_path = Path(config_file_path_override)
    elif config_file_dir_override:
      self.config_file_path = Path(config_file_dir_override, self.default_config_file_name)
    else:
      rc_dir_name = f".{app_id}rc"
      config_paths_candidates = [
          Path(self.home, rc_dir_name),
          Path(self.home),
          Path(user_config_dir()),
          Path(user_documents_dir()),
          Path(user_desktop_dir()),
          self.current_directory
        ]
      config_dir_path = next((p for p in config_paths_candidates if p.is_dir()))
      if config_dir_path == self.home:
        config_dir_path = Path(config_dir_path, rc_dir_name)
        # Does not exist b/c the order of the candidate list.
        os.mkdir(Path(config_dir_path, rc_dir_name))
      self.config_file_path = Path(config_dir_path, self.default_config_file_name)

      if not self.config_file_path.parent.exists():
        self.config_file_path.parent.mkdir()
      if not self.config_file_path.exists():
        self.config_file_path.write_text(yaml.dump(default_config))

    with open(self.config_file_path, 'r') as cf:
      self.yaml_configuration: dict[str, Any] = yaml.safe_load(cf)
