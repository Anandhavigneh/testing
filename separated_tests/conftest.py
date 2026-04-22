"""
conftest.py — Separated tests (favorite coin pairs) configuration.

Ensures the project root (d:/testing/testing) stays on sys.path so that
`config`, `clients`, and `models` are importable when pytest collects tests
from this sub-directory.
"""
import sys
import os

# Project root is one level up from this file
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
