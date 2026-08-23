"""Compatibility shim for the repository's backend repositories package.

The real repository modules live under ``backend/repositories``. This alias keeps
legacy repo-root imports working without changing the underlying package layout.
"""

from __future__ import annotations

from pathlib import Path

_backend_repositories_dir = Path(__file__).resolve().parent.parent / "backend" / "repositories"
__path__ = [str(_backend_repositories_dir)]
