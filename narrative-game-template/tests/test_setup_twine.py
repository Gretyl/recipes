"""Round 7 (test-after, network-gated): pin that the baked
``scripts/install-tweego.sh`` actually downloads a working tweego.

The install script's *shape* (uname-detect, idempotent, executable
bit) is pinned in round 3. This round pins its end-to-end behaviour:
it downloads the v2.1.1 zip from the GitHub mirror, extracts both the
binary and the bundled ``storyformats/``, and the binary executes.

Skipped by default — opt in with ``TWEEGO_NETWORK_TESTS=1`` so CI
without network access stays green and so we don't hammer the tweego
mirror on every local pytest invocation.
"""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent

NETWORK_GATE = pytest.mark.skipif(
    os.environ.get("TWEEGO_NETWORK_TESTS") != "1",
    reason="network test; set TWEEGO_NETWORK_TESTS=1 to run",
)


@pytest.fixture(scope="module")
def baked_for_install(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A fresh bake to install tweego into. Module-scoped so the
    download happens once across all tests in this file."""
    out = tmp_path_factory.mktemp("setup-twine")
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(out))
    return out / "my-narrative"


@pytest.fixture(scope="module")
def installed(baked_for_install: Path) -> Path:
    """Run the install script and return the project path."""
    result = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=baked_for_install,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"install-tweego.sh failed (rc={result.returncode}):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    return baked_for_install


@NETWORK_GATE
@pytest.mark.network
def test_install_creates_executable_binary(installed: Path) -> None:
    bin_path = installed / ".tweego" / "tweego"
    assert bin_path.is_file(), f"binary not at {bin_path}"
    mode = bin_path.stat().st_mode
    assert mode & stat.S_IXUSR, f"binary not executable: mode={oct(mode)}"


@NETWORK_GATE
@pytest.mark.network
def test_installed_tweego_emits_version(installed: Path) -> None:
    """The binary runs and prints a non-empty version string starting
    with `tweego, version`. Note: tweego's `-v` is an informational
    flag and exits 1 by design — we don't assert on the exit code,
    only that the version output is present."""
    bin_path = installed / ".tweego" / "tweego"
    result = subprocess.run(
        [str(bin_path), "-v"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    output = result.stdout + result.stderr
    assert "tweego" in output.lower(), (
        f"tweego -v output did not mention 'tweego': {output!r}"
    )
    assert "version" in output.lower(), (
        f"tweego -v output did not mention 'version': {output!r}"
    )


@NETWORK_GATE
@pytest.mark.network
@pytest.mark.parametrize("subdir", [
    "sugarcube-2",
    "harlowe-3",
    "chapbook-1",
    "snowman-2",
])
def test_installed_storyformats_include_all_bundled(
    installed: Path, subdir: str
) -> None:
    """The zip ships .tweego/storyformats/{format}-{major}/ for each of
    the four bundled formats; without these, tweego can't compile a
    story declaring `format: SugarCube` etc."""
    fmt_dir = installed / ".tweego" / "storyformats" / subdir
    assert fmt_dir.is_dir(), (
        f"missing story format {subdir} in .tweego/storyformats/ — "
        f"tweego can't compile stories declaring this format"
    )


@NETWORK_GATE
@pytest.mark.network
def test_install_is_idempotent(installed: Path) -> None:
    """Re-running install on an already-installed project succeeds and
    does not re-download (the script's idempotency contract)."""
    result = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=installed,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "already installed" in output.lower(), (
        f"second install did not skip via idempotency check: {output!r}"
    )
