from typing import Optional
import os

from salduba.util.files import resolveDir

_tests_root_name = 'tests'


def testRoot() -> Optional[str]:
  return resolveDir(_tests_root_name)