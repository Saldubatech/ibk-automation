import sys
import os
import unittest
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from salduba.ib_tws_proxy.util import LocalLogger

if __name__ == '__main__':
  localLogger = LocalLogger(level=logging.INFO)
  localLogger.setLevel(logging.INFO)
  suite = unittest.TestLoader().discover('.', pattern="test_*.py")
  unittest.TextTestRunner(verbosity=2).run(suite)
