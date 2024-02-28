import sys
import os
import unittest
import logging
from salduba.ib_tws_proxy.util import LocalLogger

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


if __name__ == '__main__':
  localLogger = LocalLogger(level=logging.INFO)
  localLogger.setLevel(logging.DEBUG)
  suite = unittest.TestLoader().discover('.', pattern="test_*.py")
  unittest.TextTestRunner(verbosity=2).run(suite)
