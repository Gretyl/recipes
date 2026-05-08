"""Round 9 (test-after, network + browser-gated): drive the baked
project's full pipeline end-to-end — bake → setup-twine → make dist →
pytest under rodney.

This is the integration gate: it proves that the template, hooks,
build script, and rodney smoke fixtures all compose into a working
system on the user's machine. Skipped by default; opt in via
``TWEEGO_NETWORK_TESTS=1`` (which also signals Chrome should be
available — rodney's headless launch needs it).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent

NETWORK_GATE = pytest.mark.skipif(
    os.environ.get("TWEEGO_NETWORK_TESTS") != "1",
    reason="end-to-end test; needs network + Chrome. "
    "Set TWEEGO_NETWORK_TESTS=1 to run.",
)


@NETWORK_GATE
@pytest.mark.network
@pytest.mark.browser
def test_baked_rodney_smoke_passes_after_full_pipeline(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """A cold bake → setup-twine → make dist → pytest path runs all
    the way through and the baked rodney smoke passes."""
    out = tmp_path_factory.mktemp("e2e-smoke")
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(out))
    project = out / "my-narrative"

    # Drive the cookbook-canonical `make test` gate, which chains
    # setup-twine → dist → pytest in one command. This mirrors what a
    # contributor running the cookbook's pre-commit gate would do.
    make_test = subprocess.run(
        ["make", "test"],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert make_test.returncode == 0, (
        f"make test failed (rc={make_test.returncode}):\n"
        f"stdout={make_test.stdout}\n"
        f"stderr={make_test.stderr}"
    )
    # Sanity: at least 2 tests passed (the two browser tests in
    # test_smoke.py — pytest's `-q` addopts suppresses individual
    # test names, but the summary line is durable).
    assert "2 passed" in make_test.stdout, (
        f"expected '2 passed' in make test output, got:\n{make_test.stdout}"
    )
