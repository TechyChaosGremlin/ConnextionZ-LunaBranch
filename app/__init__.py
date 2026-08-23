"""Compatibility shim for the repository's backend app package.

The active codebase lives under ``backend/app``. Some older tests and scripts
still import it as ``app.*`` from the repository root, so this package points the
root-level ``app`` namespace at the real backend package without changing the
actual project architecture.
"""

from __future__ import annotations

from pathlib import Path

_backend_app_dir = Path(__file__).resolve().parent.parent / "backend" / "app"
__path__ = [str(_backend_app_dir)]
