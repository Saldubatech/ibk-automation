import sys


def module_path(module_name: str) -> list[str]:
  maybeModule = sys.modules.get(module_name)
  if maybeModule:
    package = maybeModule.__package__
    if package:
      return package.split('.')
  return []
