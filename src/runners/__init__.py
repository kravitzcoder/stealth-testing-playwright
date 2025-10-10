"""
Specialized runners for each browser library

Each library has its own optimized runner!
"""

from . import base_runner
from . import playwright_runner
from . import patchright_runner
from . import camoufox_runner
from . import rebrowser_runner

__all__ = [
    'base_runner',
    'playwright_runner',
    'patchright_runner',
    'camoufox_runner',
    'rebrowser_runner'
]
