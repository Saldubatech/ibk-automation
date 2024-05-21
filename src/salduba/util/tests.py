from typing import Optional

from salduba.util.files import resolveDir

_tests_root_name = "tests"


def findTestsRoot() -> Optional[str]:
    return resolveDir(_tests_root_name)
