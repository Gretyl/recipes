"""Bake-level tests for the repo-cli cookiecutter template.

These tests programmatically run cookiecutter against the template
with both values of ``include_github_workflow`` and verify the
resulting file trees and file contents.
"""

import pathlib
import subprocess

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIRECTORY = str(pathlib.Path(__file__).parent.parent / "cookbook" / "repo-cli")


def paths(directory: pathlib.Path) -> set[str]:
    """Return a set of all relative paths (files and dirs) under *directory*."""
    all_paths = list(directory.glob("**/*"))
    return {
        str(p.relative_to(directory))
        for p in all_paths
        if str(p.relative_to(directory)) != "."
    }


class TestBakeWithWorkflow:
    """When include_github_workflow is 'yes', the full template is emitted."""

    @pytest.fixture()
    def baked(self, tmp_path: pathlib.Path) -> pathlib.Path:
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={
                "project_name": "Demo Repo CLI",
                "target_repo": "demo-repo",
                "include_github_workflow": "yes",
            },
        )
        return tmp_path / "demo-repo-cli"

    def test_output_directory_exists(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()

    def test_github_workflow_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".github" / "workflows" / "update-readme.yml").is_file()

    def test_template_module_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "demo_repo_cli" / "tui" / "template.py").is_file()

    def test_template_tests_exist(self, baked: pathlib.Path) -> None:
        assert (baked / "tests" / "test_template.py").is_file()
        assert (baked / "tests" / "test_template_apply.py").is_file()
        assert (baked / "tests" / "test_template_prepare.py").is_file()

    def test_readme_contains_placeholder(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "<template placeholder>" in readme

    def test_readme_heading(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# Demo Repo CLI")

    def test_requirements_txt_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "requirements.txt").is_file()

    def test_cli_imports_template(self, baked: pathlib.Path) -> None:
        cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
        assert "from demo_repo_cli.tui.template import template" in cli_py
        assert "cli.add_command(template)" in cli_py

    def test_pyproject_uses_target_repo(self, baked: pathlib.Path) -> None:
        pyproject = (baked / "pyproject.toml").read_text()
        assert 'name = "demo-repo-cli"' in pyproject
        assert 'demo-repo = "demo_repo_cli.tui.cli:cli"' in pyproject

    def test_workflow_uses_target_repo(self, baked: pathlib.Path) -> None:
        workflow = (baked / ".github" / "workflows" / "update-readme.yml").read_text()
        assert "demo-repo template prepare" in workflow
        assert "demo-repo template apply" in workflow

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
            check=False,
        )
        assert result.returncode == 0, (
            f"Baked tests failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_full_file_tree(self, baked: pathlib.Path) -> None:
        tree = paths(baked)
        assert ".github" in tree
        assert ".github/workflows" in tree
        assert ".github/workflows/update-readme.yml" in tree
        assert "demo_repo_cli" in tree
        assert "demo_repo_cli/tui" in tree
        assert "demo_repo_cli/tui/__init__.py" in tree
        assert "demo_repo_cli/tui/cli.py" in tree
        assert "demo_repo_cli/tui/template.py" in tree
        assert "tests" in tree
        assert "tests/test_cli.py" in tree
        assert "tests/test_template.py" in tree
        assert "tests/test_template_apply.py" in tree
        assert "tests/test_template_prepare.py" in tree
        assert "README.md" in tree
        assert "demo_repo_cli/AGENTS.md" in tree
        assert "pyproject.toml" in tree
        assert "requirements.txt" in tree
        assert ".envrc" in tree
        assert ".gitattributes" in tree
        assert "CHANGELOG.md" in tree
        assert "Makefile" in tree


class TestBakeWithoutWorkflow:
    """When include_github_workflow is 'no', only .github/ is removed.

    Template actions (template.py, tests, requirements.txt, CLI import,
    README placeholder) are still present so non-GitHub users can run
    ``<target_repo> template`` commands locally.
    """

    @pytest.fixture()
    def baked(self, tmp_path: pathlib.Path) -> pathlib.Path:
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={
                "project_name": "Demo Repo CLI",
                "target_repo": "demo-repo",
                "include_github_workflow": "no",
            },
        )
        return tmp_path / "demo-repo-cli"

    def test_output_directory_exists(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()

    def test_no_github_directory(self, baked: pathlib.Path) -> None:
        assert not (baked / ".github").exists()

    def test_template_module_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "demo_repo_cli" / "tui" / "template.py").is_file()

    def test_template_tests_exist(self, baked: pathlib.Path) -> None:
        assert (baked / "tests" / "test_template.py").is_file()
        assert (baked / "tests" / "test_template_apply.py").is_file()
        assert (baked / "tests" / "test_template_prepare.py").is_file()

    def test_requirements_txt_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "requirements.txt").is_file()

    def test_readme_contains_placeholder(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "<template placeholder>" in readme

    def test_readme_heading(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# Demo Repo CLI")

    def test_cli_imports_template(self, baked: pathlib.Path) -> None:
        cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
        assert "from demo_repo_cli.tui.template import template" in cli_py
        assert "cli.add_command(template)" in cli_py

    def test_core_files_still_exist(self, baked: pathlib.Path) -> None:
        assert (baked / "demo_repo_cli" / "tui" / "__init__.py").is_file()
        assert (baked / "demo_repo_cli" / "tui" / "cli.py").is_file()
        assert (baked / "pyproject.toml").is_file()
        assert (baked / "README.md").is_file()
        assert (baked / "demo_repo_cli" / "AGENTS.md").is_file()

    def test_full_file_tree(self, baked: pathlib.Path) -> None:
        tree = paths(baked)
        # These should be present (everything except .github/)
        assert "demo_repo_cli" in tree
        assert "demo_repo_cli/tui" in tree
        assert "demo_repo_cli/tui/__init__.py" in tree
        assert "demo_repo_cli/tui/cli.py" in tree
        assert "demo_repo_cli/tui/template.py" in tree
        assert "tests" in tree
        assert "tests/test_cli.py" in tree
        assert "tests/test_template.py" in tree
        assert "tests/test_template_apply.py" in tree
        assert "tests/test_template_prepare.py" in tree
        assert "README.md" in tree
        assert "demo_repo_cli/AGENTS.md" in tree
        assert "pyproject.toml" in tree
        assert "requirements.txt" in tree
        assert ".envrc" in tree
        assert ".gitattributes" in tree
        assert "CHANGELOG.md" in tree
        assert "Makefile" in tree
        # Only .github/ should NOT be present
        assert ".github" not in tree
