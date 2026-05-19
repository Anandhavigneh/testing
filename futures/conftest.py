"""
conftest.py — Futures test configuration.
Inserts the project root into sys.path so that `config`, `futures_client`, and `models`
are importable when pytest collects tests from this subdirectory.
"""
import sys
import os

# Ensure project root (d:/testing/testing) is always on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
