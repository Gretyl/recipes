"""Round 3: pin the build harness produced by a default bake.

Beyond the source passages (round 2), a baked project ships:

- a ``Makefile`` exposing ``setup-twine``, ``dist``, ``test``, ``clean``
  — the same toolchain-detect-or-skip idiom from the grimoire repo's
  ``evolution-trust-simulations/Makefile`` (per docs/non-python-toolchains.md "Non-Python
  toolchains" pattern), reading ``TWEEGO`` rather than ``NODE``.
  ``test`` is the single pre-commit gate per Gretyl/recipes cookbook
  convention.
- a ``pyproject.toml`` declaring rodney + pytest as dev deps for the
  baked rodney smoke test (round 9);
- ``scripts/install-tweego.sh`` (executable) — downloads the right
  platform tweego release into ``.tweego/`` per AGENTS.md
  ``setup-<lang>`` idempotency rule;
- a ``.gitignore`` that excludes ``dist/`` and ``.tweego/``;
- a ``README.md`` (non-empty, mentions "tweego");
- a ``tests/`` directory with ``conftest.py`` and ``test_smoke.py``
  (the rodney smoke; assertions filled in round 9).
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def baked_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output_dir = tmp_path_factory.mktemp("bake-harness")
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(output_dir),
    )
    project = output_dir / "my-narrative"
    assert project.is_dir(), f"bake did not create {project}"
    return project


REQUIRED_HARNESS_FILES = [
    "Makefile",
    "pyproject.toml",
    "README.md",
    ".gitignore",
    "scripts/install-tweego.sh",
    "tests/conftest.py",
    "tests/test_smoke.py",
]


@pytest.mark.parametrize("relpath", REQUIRED_HARNESS_FILES)
def test_harness_file_exists_and_nonempty(baked_project: Path, relpath: str) -> None:
    target = baked_project / relpath
    assert target.is_file(), f"missing harness file: {relpath}"
    assert target.read_text().strip(), f"harness file {relpath} is empty"


def test_install_tweego_script_is_executable(baked_project: Path) -> None:
    script = baked_project / "scripts" / "install-tweego.sh"
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR, f"install-tweego.sh is not executable (mode={oct(mode)})"


def test_makefile_declares_setup_twine_target(baked_project: Path) -> None:
    content = (baked_project / "Makefile").read_text()
    assert "setup-twine:" in content, "Makefile must declare a `setup-twine:` target"


def test_makefile_declares_dist_target(baked_project: Path) -> None:
    content = (baked_project / "Makefile").read_text()
    # Pattern rule or explicit; either is acceptable, but `dist` must appear
    # as a real target (not just inside a comment).
    nonblank_lines = [
        line for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert any(line.startswith("dist") and ":" in line for line in nonblank_lines), (
        "Makefile must declare a `dist` target"
    )


def test_makefile_declares_test_target(baked_project: Path) -> None:
    """Per Gretyl/recipes cookbook AGENTS.md, generated projects expose
    `make test` as the single pre-commit gate."""
    content = (baked_project / "Makefile").read_text()
    assert "test:" in content, (
        "Makefile must declare a `test:` target — the cookbook's single "
        "pre-commit gate"
    )


def test_makefile_declares_clean_target(baked_project: Path) -> None:
    content = (baked_project / "Makefile").read_text()
    assert "clean:" in content, "Makefile must declare a `clean:` target"


def test_makefile_uses_tweego_detection_idiom(baked_project: Path) -> None:
    """Mirrors evolution-trust-simulations' `NODE := $(shell command -v ...)`
    pattern from the grimoire repo, with TWEEGO as the tool variable."""
    content = (baked_project / "Makefile").read_text()
    assert "TWEEGO" in content, (
        "Makefile must reference a TWEEGO variable for toolchain detection"
    )
    assert "command -v tweego" in content, (
        "Makefile must detect tweego via `command -v tweego` per AGENTS.md "
        "'Non-Python toolchains' pattern"
    )
    assert "ifdef TWEEGO" in content or "ifeq" in content, (
        "Makefile must guard tweego-dependent targets so machines without "
        "the toolchain skip cleanly"
    )


def test_gitignore_excludes_build_artifacts(baked_project: Path) -> None:
    content = (baked_project / ".gitignore").read_text()
    for pattern in ("dist/", ".tweego/"):
        assert pattern in content, (
            f".gitignore must exclude {pattern!r} (build artifact)"
        )


def test_baked_pyproject_declares_rodney_dev_dep(baked_project: Path) -> None:
    """The baked rodney smoke test (round 9) needs rodney as a dev dep."""
    content = (baked_project / "pyproject.toml").read_text()
    assert "rodney" in content.lower(), (
        "baked pyproject.toml must declare rodney as a dev dependency"
    )
    assert "pytest" in content, "baked pyproject.toml must declare pytest"


def test_install_tweego_detects_platform(baked_project: Path) -> None:
    """The install script must branch on `uname -s` / `uname -m` to pick
    the right release archive — without that, the binary downloaded on
    a darwin-arm64 host could be a linux-x64 ELF and fail silently."""
    content = (baked_project / "scripts" / "install-tweego.sh").read_text()
    assert "uname" in content, "install-tweego.sh must inspect `uname` for OS/arch"


def test_readme_mentions_tweego(baked_project: Path) -> None:
    """The baked README guides the author through the tweego workflow."""
    content = (baked_project / "README.md").read_text().lower()
    assert "tweego" in content, "baked README.md must mention tweego (the build tool)"
