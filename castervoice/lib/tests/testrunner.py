import os
import sys
import unittest

from dragonfly.engines import _engines_by_name, get_engine

if not _engines_by_name:
    engine = get_engine("text")
    engine.connect()

def get_master_suite():
    return unittest.defaultTestLoader.discover(os.path.dirname(__file__))

def run_tests():
    result = unittest.TextTestRunner(verbosity=2).run(get_master_suite())
    return result

if __name__ == '__main__':
    sys.exit(len(run_tests().failures))
