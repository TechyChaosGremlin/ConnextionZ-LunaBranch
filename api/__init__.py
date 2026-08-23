"""Compatibility shim for the repository's backend API package.

The real GraphQL API module lives under ``backend/api``. Some older code paths
still import it as ``api.*`` from the repository root, so this package points the
root-level namespace to the actual backend API package without changing the
project architecture.
"""

from __future__ import annotations

from pathlib import Path

_backend_api_dir = Path(__file__).resolve().parent.parent / "backend" / "api"
__path__ = [str(_backend_api_dir)]
