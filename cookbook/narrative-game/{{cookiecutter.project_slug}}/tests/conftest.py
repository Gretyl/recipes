"""Pytest configuration for {{ cookiecutter.project_slug }} tests.

The browser smoke (`test_smoke.py`) drives a real headless Chrome via
the `rodney` CLI; that takes a few seconds to start, so we use a
session-scoped fixture (defined inside the test module) rather than
loading rodney here. This file exists as the documented hook point —
add fixtures for new tests as the story grows.
"""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
DIST_HTML = PROJECT_ROOT / "dist" / "index.html"


@pytest.fixture(scope="session")
def dist_html() -> Path:
    """Path to the compiled story HTML. Tests using this fixture skip
    cleanly if the build has not been run yet."""
    if not DIST_HTML.is_file():
        pytest.skip(
            f"{DIST_HTML} not found — run `make setup-twine && make dist` first"
        )
    return DIST_HTML
