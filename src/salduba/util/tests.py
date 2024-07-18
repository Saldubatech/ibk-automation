import os
import sys
from typing import Optional

_tests_root_name = "tests"


def findTestsRoot() -> Optional[str]:
  for directory in sys.path:
    path = os.path.join(directory, _tests_root_name)
    if os.path.isdir(path):
      return path
  return None
