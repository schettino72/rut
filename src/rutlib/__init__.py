"""
rut - Run Unit Tests

A modern test runner for Python's unittest framework.
"""

__all__ = ["RutCLI", "RutRunner", "WarningCollector", "RutError", "InvalidAsyncTestError"]
__version__ = "1.0.0"
__license__ = "MIT"
__author__ = "Eduardo Naufel Schettino"
__author_email__ = "schettino72@gmail.com"
__url__ = "https://github.com/schettino72/rut"

from .cli import RutCLI
from .runner import RutRunner, WarningCollector, RutError, InvalidAsyncTestError
