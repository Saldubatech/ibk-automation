import sys
import os
import logging

cwd = os.getcwd()
print(f"CWD: {cwd}")
sys.path.append(cwd)

from salduba.corvino.update_symbols import update_symbols

if __name__ == "__main__":
  logging.basicConfig(level=logging.WARN)
  logging.info('Executing Update Symbols')
  update_symbols('collect_symbols_config.yml', None, True)
