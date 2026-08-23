from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_app_import_works_when_run_from_backend_directory() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"

    result = subprocess.run(
        [sys.executable, "-c", "import app.main; print(app.main.app.title)"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert "ConnextionZ Profile API" in result.stdout
