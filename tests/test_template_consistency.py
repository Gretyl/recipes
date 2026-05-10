"""Cross-template consistency tests.

These tests verify that shared conventions (Python version, mypy settings,
dev dependencies, build backend) stay in sync between the python-project
and repo-cli templates, and that every cookbook entry honors the
discovery-based MVP guidance contract.
"""

import pathlib
import re
import shutil
import subprocess

import pytest

from tests.helpers import bake

COOKBOOK = pathlib.Path(__file__).parent.parent / "cookbook"
PP_PYPROJECT = (
    COOKBOOK / "python-project" / "{{cookiecutter.project_slug}}" / "pyproject.toml"
)
RC_PYPROJECT = (
    COOKBOOK / "repo-cli" / "{{cookiecutter.project_slug}}" / "pyproject.toml"
)


def _discover_cookbook_templates() -> list[str]:
    """Enumerate every cookbook entry that is a valid cookiecutter template.

    A directory directly under ``cookbook/`` qualifies if it contains a
    ``cookiecutter.json``. Discovery happens at collection time so a
    newly added template is picked up automatically; the MVP guidance
    contract below applies to it without any registration step.
    """
    return sorted(
        d.name
        for d in COOKBOOK.iterdir()
        if d.is_dir() and (d / "cookiecutter.json").is_file()
    )


COOKBOOK_TEMPLATES = _discover_cookbook_templates()


def _extract_section(text: str, header: str) -> str:
    """Extract a TOML section by header, returning lines until next section."""
    lines = text.splitlines()
    collecting = False
    result: list[str] = []
    for line in lines:
        if line.strip() == header:
            collecting = True
            continue
        if collecting:
            if line.startswith("[") and not line.startswith("[["):
                break
            result.append(line)
    return "\n".join(result).strip()


def _extract_value(text: str, key: str) -> str:
    """Extract a single key = value from TOML text."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith((f"{key} =", f"{key}=")):
            return stripped.split("=", 1)[1].strip().strip('"')
    msg = f"Key {key!r} not found"
    raise KeyError(msg)


class TestPythonVersionParity:
    """Both templates must target the same Python version."""

    def test_requires_python_matches(self) -> None:
        pp = _extract_value(PP_PYPROJECT.read_text(), "requires-python")
        rc = _extract_value(RC_PYPROJECT.read_text(), "requires-python")
        assert pp == rc, f"python-project: {pp}, repo-cli: {rc}"

    def test_mypy_python_version_matches(self) -> None:
        pp = _extract_value(PP_PYPROJECT.read_text(), "python_version")
        rc = _extract_value(RC_PYPROJECT.read_text(), "python_version")
        assert pp == rc, f"python-project: {pp}, repo-cli: {rc}"


class TestMypyStrictSettings:
    """Both templates must use identical strict mypy settings."""

    def test_mypy_settings_match(self) -> None:
        pp_mypy = _extract_section(PP_PYPROJECT.read_text(), "[tool.mypy]")
        rc_mypy = _extract_section(RC_PYPROJECT.read_text(), "[tool.mypy]")
        assert pp_mypy == rc_mypy, (
            f"mypy settings differ:\npython-project:\n{pp_mypy}\n\nrepo-cli:\n{rc_mypy}"
        )


class TestDevDependencyBaseline:
    """Both templates must include the same core dev tool set."""

    def test_shared_dev_dependencies(self) -> None:
        required = {"pytest", "pytest-cov", "pytest-mock", "ruff", "mypy"}
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = path.read_text()
            dev_section = _extract_section(text, "[dependency-groups]")
            for dep in required:
                assert f'"{dep}"' in dev_section, (
                    f"{name} template missing dev dependency: {dep}"
                )


class TestBuildBackendMatch:
    """Both templates must use the same build backend."""

    def test_build_backend_is_hatchling(self) -> None:
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = path.read_text()
            assert 'build-backend = "hatchling.build"' in text, (
                f"{name} template does not use hatchling"
            )


class TestDependencyMatch:
    """Both templates must include the same runtime dependencies."""

    def test_click_in_both(self) -> None:
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = path.read_text()
            assert '"click"' in text, f"{name} missing click dependency"

    def test_pydantic_in_both(self) -> None:
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = path.read_text()
            assert '"pydantic"' in text, f"{name} missing pydantic dependency"


class TestPerTemplateAgentGuidance:
    """Discovery-based MVP contract for per-template agent guidance.

    Three properties are enforced across every cookbook entry:

    1. **AGENTS.md exists** somewhere in the bake. Project root is
       canonical for standalone templates; subpackage-merge templates
       like `repo-cli` ship it under the package directory. Either
       layout is acceptable — the contract is that agent-only guidance
       has a home.
    2. **CLAUDE.md, if present, is a one-line `@AGENTS.md` redirect**
       resolving to a sibling AGENTS.md. CLAUDE.md is optional; a
       template that doesn't ship one is silently fine. A template that
       *does* must point at a real AGENTS.md so both filenames resolve
       to the same guidance.
    3. **If the bake declares a Python project** (i.e., a `pyproject.toml`
       at the project root), the bake's own pytest suite must produce
       non-zero passing tests. This is the slow integration check —
       the bake's punched-out tests must actually run green out of the
       box.

    The template list is discovered dynamically from `cookbook/` at
    collection time; a fifth template added without honoring the
    contract lands red automatically.
    """

    @pytest.mark.parametrize("template", COOKBOOK_TEMPLATES)
    def test_baked_ships_agents_md(self, tmp_path: pathlib.Path, template: str) -> None:
        baked = bake(template, tmp_path)
        candidates = list(baked.rglob("AGENTS.md"))
        assert candidates, (
            f"{template} bake must ship at least one AGENTS.md — "
            "agent-only conventions per the cookbook MVP contract"
        )

    @pytest.mark.parametrize("template", COOKBOOK_TEMPLATES)
    def test_claude_md_redirects_if_present(
        self, tmp_path: pathlib.Path, template: str
    ) -> None:
        baked = bake(template, tmp_path)
        for claude in baked.rglob("CLAUDE.md"):
            content = claude.read_text().strip()
            assert content == "@AGENTS.md", (
                f"{template}'s {claude.relative_to(baked)} must be a one-line "
                f"`@AGENTS.md` redirect, got: {content!r}"
            )
            sibling_agents = claude.parent / "AGENTS.md"
            assert sibling_agents.is_file(), (
                f"{template}'s {claude.relative_to(baked)} redirects to "
                f"`@AGENTS.md` but no sibling AGENTS.md exists at "
                f"{sibling_agents.relative_to(baked)}"
            )

    @pytest.mark.slow()
    @pytest.mark.skipif(shutil.which("uv") is None, reason="uv not installed")
    @pytest.mark.parametrize("template", COOKBOOK_TEMPLATES)
    def test_python_template_baked_pytest_runs_green(
        self, tmp_path: pathlib.Path, template: str
    ) -> None:
        baked = bake(template, tmp_path)
        if not (baked / "pyproject.toml").is_file():
            pytest.skip(f"{template} is not a Python template")
        if not (baked / "tests").is_dir():
            pytest.fail(f"{template} declares pyproject.toml but ships no tests/ dir")
        subprocess.run(["uv", "sync"], cwd=baked, check=True, capture_output=True)
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/"],
            cwd=baked,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"{template}'s baked pytest exited {result.returncode}:\n"
            f"--- stdout ---\n{result.stdout}\n"
            f"--- stderr ---\n{result.stderr}"
        )
        match = re.search(r"(\d+) passed", result.stdout)
        assert match is not None and int(match.group(1)) > 0, (
            f"{template}'s baked pytest produced 0 passing tests — "
            f"'representative coverage' requires non-zero passing.\n"
            f"--- stdout ---\n{result.stdout}"
        )
