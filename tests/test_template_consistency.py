"""Cross-template consistency tests.

These tests verify that shared conventions (Python version, mypy settings,
dev dependencies, build backend) stay in sync between the python-project
and repo-cli templates.
"""

import pathlib

COOKBOOK = pathlib.Path(__file__).parent.parent / "cookbook"
PP_PYPROJECT = (
    COOKBOOK
    / "python-project"
    / "{{cookiecutter.project_slug}}"
    / "pyproject.toml"
)
RC_PYPROJECT = (
    COOKBOOK
    / "repo-cli"
    / "{{cookiecutter.project_slug}}"
    / "pyproject.toml"
)


def _read(path: pathlib.Path) -> str:
    return path.read_text()


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
        if stripped.startswith(f"{key} =") or stripped.startswith(f"{key}="):
            return stripped.split("=", 1)[1].strip().strip('"')
    msg = f"Key {key!r} not found"
    raise KeyError(msg)


class TestPythonVersionParity:
    """Both templates must target the same Python version."""

    def test_requires_python_matches(self) -> None:
        pp = _extract_value(_read(PP_PYPROJECT), "requires-python")
        rc = _extract_value(_read(RC_PYPROJECT), "requires-python")
        assert pp == rc, f"python-project: {pp}, repo-cli: {rc}"

    def test_mypy_python_version_matches(self) -> None:
        pp = _extract_value(_read(PP_PYPROJECT), "python_version")
        rc = _extract_value(_read(RC_PYPROJECT), "python_version")
        assert pp == rc, f"python-project: {pp}, repo-cli: {rc}"


class TestMypyStrictSettings:
    """Both templates must use identical strict mypy settings."""

    def test_mypy_settings_match(self) -> None:
        pp_mypy = _extract_section(_read(PP_PYPROJECT), "[tool.mypy]")
        rc_mypy = _extract_section(_read(RC_PYPROJECT), "[tool.mypy]")
        assert pp_mypy == rc_mypy, (
            f"mypy settings differ:\npython-project:\n{pp_mypy}\n\n"
            f"repo-cli:\n{rc_mypy}"
        )


class TestDevDependencyBaseline:
    """Both templates must include the same core dev tool set."""

    def test_shared_dev_dependencies(self) -> None:
        required = {"pytest", "pytest-cov", "pytest-mock", "ruff", "mypy"}
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = _read(path)
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
            text = _read(path)
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
            text = _read(path)
            assert '"click"' in text, f"{name} missing click dependency"

    def test_pydantic_in_both(self) -> None:
        for name, path in [
            ("python-project", PP_PYPROJECT),
            ("repo-cli", RC_PYPROJECT),
        ]:
            text = _read(path)
            assert '"pydantic"' in text, f"{name} missing pydantic dependency"
