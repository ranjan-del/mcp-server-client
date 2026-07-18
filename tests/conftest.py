"""Pytest configuration: make the repo root importable.

The tests import ``server.tools.*`` etc., so the repo root must be on sys.path
regardless of where pytest is invoked from.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
