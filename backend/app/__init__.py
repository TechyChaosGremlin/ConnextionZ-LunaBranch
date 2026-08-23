"""ConnextionZ profile backend package.

This package is intentionally laid out as ``backend.app`` to match the current
project architecture. Some legacy test code and older modules still import it as
``app`` from the repository root, so we keep a compatibility alias for both
import paths without changing the actual package structure.
"""

from __future__ import annotations

import sys

# Keep both import styles working: ``import backend.app.main`` and
# ``import app.main`` resolve to the same package object.
if __package__ and __package__.startswith("backend"):
    if "app" not in sys.modules or sys.modules["app"] is not sys.modules[__name__]:
        sys.modules["app"] = sys.modules[__name__]
