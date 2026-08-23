"""Compatibility shim for the repository's backend feature package.

The real feature modules live under ``backend/features``. Some code paths still
import them as ``features.*`` from the repository root, so this package points the
root-level namespace to the existing backend package layout without altering the
actual architecture.
"""

from __future__ import annotations

from pathlib import Path

_backend_features_dir = Path(__file__).resolve().parent.parent / "backend" / "features"
__path__ = [str(_backend_features_dir)]
