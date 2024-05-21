import os.path
import sys
from pathlib import Path
from typing import Optional


def resolveFileInPath(filename: str) -> Optional[Path]:
  for directory in sys.path:
    path = Path(directory, filename)
    if path.exists() and path.is_file():
      return path
  return None


def resolveDir(dirname: str) -> Optional[str]:
  for directory in sys.path:
    path = os.path.join(directory, dirname)
    if os.path.isdir(path):
      return path
  return None
