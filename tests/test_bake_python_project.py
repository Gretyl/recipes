"""Bake-level tests for the python-project cookiecutter template.

These tests programmatically run cookiecutter against the template
with default and custom contexts, then verify the resulting file
trees and file contents.
"""

import pathlib
import subprocess

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIRECTORY = str(
    pathlib.Path(__file__).parent.parent / "cookbook" / "python-project"
)


def paths(directory: pathlib.Path) -> set[str]:
    """Return a set of all relative paths (files and dirs) under *directory*."""
    all_paths = list(directory.glob("**/*"))
    return {
        str(p.relative_to(directory))
        for p in all_paths
        if str(p.relative_to(directory)) != "."
    }


class TestBakeDefaults:
    """Bake with default context values from cookiecutter.json."""

    @pytest.fixture()
    def baked(self, tmp_path: pathlib.Path) -> pathlib.Path:
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
        )
        return tmp_path / "fresh-project"

    def test_output_directory_exists(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()

    def test_package_directory_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "fresh_project").is_dir()

    def test_init_exports_hello_world(self, baked: pathlib.Path) -> None:
        init_py = (baked / "fresh_project" / "__init__.py").read_text()
        assert "hello_world" in init_py

    def test_main_module_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "fresh_project" / "main.py").is_file()

    def test_main_module_has_hello_world(self, baked: pathlib.Path) -> None:
        main_py = (baked / "fresh_project" / "main.py").read_text()
        assert "def hello_world()" in main_py

    def test_main_module_has_main(self, baked: pathlib.Path) -> None:
        main_py = (baked / "fresh_project" / "main.py").read_text()
        assert "def main()" in main_py

    def test_test_file_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "tests" / "test_main.py").is_file()

    def test_test_imports_package(self, baked: pathlib.Path) -> None:
        test_py = (baked / "tests" / "test_main.py").read_text()
        assert "from fresh_project.main import hello_world" in test_py

    def test_test_has_return_annotation(self, baked: pathlib.Path) -> None:
        """Test functions must have -> None for strict mypy."""
        test_py = (baked / "tests" / "test_main.py").read_text()
        assert "-> None:" in test_py

    def test_pyproject_name(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'name = "fresh-project"' in pyproject

    def test_pyproject_description(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'description = "My take on Fresh Project"' in pyproject

    def test_pyproject_python_version(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'requires-python = ">=3.13"' in pyproject

    def test_pyproject_hatchling_backend(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'build-backend = "hatchling.build"' in pyproject

    def test_pyproject_click_dependency(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert '"click"' in pyproject

    def test_pyproject_pydantic_dependency(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert '"pydantic"' in pyproject

    def test_pyproject_mypy_strict(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert "disallow_untyped_defs = true" in pyproject

    def test_pyproject_mypy_overrides_package(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'module = "fresh_project.*"' in pyproject

    def test_readme_heading(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# fresh_project")

    def test_readme_has_quickstart(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "uv sync && direnv allow" in readme

    def test_makefile_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "Makefile").is_file()

    def test_makefile_test_target(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        assert "--cov=fresh_project" in makefile
        assert "$(PYTHON_DIRS)" in makefile.split("test:")[1].split("\n\n")[0]

    def test_makefile_python_dirs(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        assert "PYTHON_DIRS = fresh_project/ tests/" in makefile

    def test_docs_spec_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "docs" / "spec.md").is_file()

    def test_scripts_dir_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "scripts" / "make_cookiecutter_template.py").is_file()

    def test_envrc_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".envrc").is_file()

    def test_gitignore_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".gitignore").is_file()

    def test_gitattributes_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".gitattributes").is_file()

    def test_full_file_tree(self, baked: pathlib.Path) -> None:
        tree = paths(baked)
        assert "fresh_project" in tree
        assert "fresh_project/__init__.py" in tree
        assert "fresh_project/main.py" in tree
        assert "tests" in tree
        assert "tests/test_main.py" in tree
        assert "docs" in tree
        assert "docs/spec.md" in tree
        assert "scripts" in tree
        assert "scripts/make_cookiecutter_template.py" in tree
        assert "pyproject.toml" in tree
        assert "README.md" in tree
        assert "Makefile" in tree
        assert ".envrc" in tree
        assert ".gitattributes" in tree
        assert ".gitignore" in tree

    def test_no_raw_template_variables(self, baked: pathlib.Path) -> None:
        """No file should contain un-rendered cookiecutter variables."""
        for p in baked.rglob("*"):
            if p.is_file():
                try:
                    text = p.read_text()
                except UnicodeDecodeError:
                    continue
                assert "{{cookiecutter." not in text, (
                    f"{p.relative_to(baked)} contains un-rendered template variable"
                )

    @pytest.mark.slow()
    def test_baked_tests_pass(self, baked: pathlib.Path) -> None:
        """The baked project's own test suite must pass."""
        subprocess.run(
            ["uv", "sync"],
            cwd=baked,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["uv", "run", "pytest", "-x", "-q"],
            cwd=baked,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Baked tests failed:\n{result.stdout}\n{result.stderr}"
        )


class TestBakeCustomContext:
    """Bake with custom context to verify variable substitution."""

    @pytest.fixture()
    def baked(self, tmp_path: pathlib.Path) -> pathlib.Path:
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={
                "project_name": "Widget Factory",
                "project_slug": "widget-factory",
                "package_name": "widget_factory",
            },
        )
        return tmp_path / "widget-factory"

    def test_output_directory_named_by_slug(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()

    def test_package_directory_named_by_package(self, baked: pathlib.Path) -> None:
        assert (baked / "widget_factory").is_dir()
        assert (baked / "widget_factory" / "__init__.py").is_file()
        assert (baked / "widget_factory" / "main.py").is_file()

    def test_pyproject_uses_custom_slug(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'name = "widget-factory"' in pyproject

    def test_pyproject_uses_custom_name(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'description = "My take on Widget Factory"' in pyproject

    def test_pyproject_mypy_overrides_custom_package(
        self, baked: pathlib.Path
    ) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'module = "widget_factory.*"' in pyproject

    def test_test_imports_custom_package(self, baked: pathlib.Path) -> None:
        test_py = (baked / "tests" / "test_main.py").read_text()
        assert "from widget_factory.main import hello_world" in test_py

    def test_makefile_coverage_uses_custom_package(
        self, baked: pathlib.Path
    ) -> None:
        makefile = (baked / "Makefile").read_text()
        assert "--cov=widget_factory" in makefile

    def test_readme_heading_uses_custom_package(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# widget_factory")

    def test_no_default_values_leak(self, baked: pathlib.Path) -> None:
        """Ensure default 'fresh_project' doesn't appear in custom bake."""
        for p in baked.rglob("*"):
            if p.is_file():
                try:
                    text = p.read_text()
                except UnicodeDecodeError:
                    continue
                assert "fresh_project" not in text, (
                    f"{p.relative_to(baked)} contains default value 'fresh_project'"
                )
                assert "fresh-project" not in text, (
                    f"{p.relative_to(baked)} contains default value 'fresh-project'"
                )
                assert "Fresh Project" not in text, (
                    f"{p.relative_to(baked)} contains default value 'Fresh Project'"
                )
