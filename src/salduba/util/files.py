import os.path
import sys
from typing import Optional


def resolveFile(filename: str) -> Optional[str]:
    for directory in sys.path:
        path = os.path.join(directory, filename)
        if os.path.isfile(path):
            return path
    return None


def resolveDir(dirname: str) -> Optional[str]:
    for directory in sys.path:
        path = os.path.join(directory, dirname)
        if os.path.isdir(path):
            return path
    return None
