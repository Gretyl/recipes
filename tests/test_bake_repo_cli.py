"""Bake-level tests for the repo-cli cookiecutter template.

These tests programmatically run cookiecutter against the template
with both values of ``include_github_workflows`` and verify the
resulting file trees and file contents.
"""

import pathlib
import subprocess

import pytest

from tests.helpers import bake, makefile_recipe, mermaid_block, paths


def _bake(tmp_path: pathlib.Path, *, workflow: str) -> pathlib.Path:
    return bake(
        "repo-cli",
        tmp_path,
        extra_context={
            "project_name": "Demo Repo CLI",
            "target_repo": "demo-repo",
            "include_github_workflows": workflow,
        },
    )


# ---------------------------------------------------------------------------
# Shared tests — run for both workflow=yes and workflow=no
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", params=["yes", "no"])
def baked(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> pathlib.Path:
    return _bake(tmp_path_factory.mktemp("shared"), workflow=request.param)


def test_output_directory_exists(baked: pathlib.Path) -> None:
    assert baked.is_dir()


def test_template_module_exists(baked: pathlib.Path) -> None:
    assert (baked / "demo_repo_cli" / "tui" / "template.py").is_file()


def test_template_tests_exist(baked: pathlib.Path) -> None:
    assert (baked / "tests" / "test_template.py").is_file()
    assert (baked / "tests" / "test_template_apply.py").is_file()
    assert (baked / "tests" / "test_template_prepare.py").is_file()


def test_readme_contains_placeholder(baked: pathlib.Path) -> None:
    readme = (baked / "README.md").read_text()
    assert "<template placeholder>" in readme


def test_readme_heading(baked: pathlib.Path) -> None:
    readme = (baked / "README.md").read_text()
    assert readme.startswith("# Demo Repo CLI")


def test_requirements_txt_exists(baked: pathlib.Path) -> None:
    assert (baked / "requirements.txt").is_file()


def test_cli_imports_template(baked: pathlib.Path) -> None:
    cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
    assert "from demo_repo_cli.tui.template import template" in cli_py
    assert "cli.add_command(template)" in cli_py


def test_status_module_exists(baked: pathlib.Path) -> None:
    assert (baked / "demo_repo_cli" / "tui" / "status.py").is_file()


def test_dashboard_module_exists(baked: pathlib.Path) -> None:
    assert (baked / "demo_repo_cli" / "tui" / "dashboard.py").is_file()


def test_status_tests_exist(baked: pathlib.Path) -> None:
    assert (baked / "tests" / "test_status.py").is_file()


def test_dashboard_tests_exist(baked: pathlib.Path) -> None:
    assert (baked / "tests" / "test_dashboard.py").is_file()


def test_cli_imports_status(baked: pathlib.Path) -> None:
    cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
    assert "from demo_repo_cli.tui.status import status" in cli_py
    assert "cli.add_command(status)" in cli_py


def test_cli_imports_dashboard(baked: pathlib.Path) -> None:
    cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
    assert "from demo_repo_cli.tui.dashboard import dashboard" in cli_py
    assert "cli.add_command(dashboard)" in cli_py


def test_pyproject_rich_dev_dependency(baked: pathlib.Path) -> None:
    pyproject = (baked / "pyproject.toml").read_text()
    assert '"rich"' in pyproject


def test_pyproject_textual_dev_dependency(baked: pathlib.Path) -> None:
    pyproject = (baked / "pyproject.toml").read_text()
    assert '"textual"' in pyproject


def test_core_files_exist(baked: pathlib.Path) -> None:
    assert (baked / "demo_repo_cli" / "tui" / "__init__.py").is_file()
    assert (baked / "demo_repo_cli" / "tui" / "cli.py").is_file()
    assert (baked / "pyproject.toml").is_file()
    assert (baked / "README.md").is_file()
    assert (baked / "demo_repo_cli" / "AGENTS.md").is_file()


def test_no_raw_template_variables(baked: pathlib.Path) -> None:
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


def test_shared_file_tree(baked: pathlib.Path) -> None:
    """Core files present regardless of workflow setting."""
    tree = paths(baked)
    assert "demo_repo_cli" in tree
    assert "demo_repo_cli/tui" in tree
    assert "demo_repo_cli/tui/__init__.py" in tree
    assert "demo_repo_cli/tui/cli.py" in tree
    assert "demo_repo_cli/tui/dashboard.py" in tree
    assert "demo_repo_cli/tui/status.py" in tree
    assert "demo_repo_cli/tui/template.py" in tree
    assert "tests" in tree
    assert "tests/test_cli.py" in tree
    assert "tests/test_dashboard.py" in tree
    assert "tests/test_status.py" in tree
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


# ---------------------------------------------------------------------------
# Workflow-only tests
# ---------------------------------------------------------------------------


class TestBakeWithWorkflow:
    """Tests specific to include_github_workflows='yes'."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return _bake(tmp_path_factory.mktemp("workflow"), workflow="yes")

    def test_github_workflow_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".github" / "workflows" / "update-readme.yml").is_file()

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

    def test_full_file_tree_includes_github(self, baked: pathlib.Path) -> None:
        tree = paths(baked)
        assert ".github" in tree
        assert ".github/workflows" in tree
        assert ".github/workflows/update-readme.yml" in tree

    def test_ci_workflow_exists(self, baked: pathlib.Path) -> None:
        """ci.yml ships alongside update-readme.yml when the flag is 'yes'."""
        assert (baked / ".github" / "workflows" / "ci.yml").is_file()

    def test_ci_workflow_invokes_make_setup_ci(self, baked: pathlib.Path) -> None:
        """Propagation: ci.yml routes install through make setup-ci."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make setup-ci" in yml

    def test_ci_workflow_invokes_make_test(self, baked: pathlib.Path) -> None:
        """Propagation: renaming the Makefile test target would break CI."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make test" in yml

    def test_makefile_defines_setup_ci_target(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        assert "setup-ci:" in makefile

    def test_makefile_setup_ci_runs_uv_sync_frozen(self, baked: pathlib.Path) -> None:
        """setup-ci uses --frozen to enforce lockfile fidelity in CI."""
        makefile = (baked / "Makefile").read_text()
        assert "uv sync --frozen" in makefile_recipe(makefile, "setup-ci")

    def test_makefile_setup_ci_is_phony(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        phony_line = next(
            line for line in makefile.splitlines() if line.startswith(".PHONY:")
        )
        assert "setup-ci" in phony_line

    def test_makefile_help_lists_setup_ci(self, baked: pathlib.Path) -> None:
        """Propagation: make help must advertise the new target."""
        makefile = (baked / "Makefile").read_text()
        assert '"setup-ci"' in makefile

    def test_readme_has_ci_section(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "## CI" in readme

    def test_readme_ci_section_names_both_workflows(self, baked: pathlib.Path) -> None:
        """Propagation: README must name both workflow files the flag ships."""
        readme = (baked / "README.md").read_text()
        assert "update-readme.yml" in readme
        assert "ci.yml" in readme

    def test_readme_ci_section_names_setup_ci_target(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "make setup-ci" in readme

    def test_readme_ci_section_has_mermaid_flowchart(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "```mermaid" in readme
        assert "flowchart" in readme

    def test_readme_mermaid_names_setup_ci_test_and_cog(
        self, baked: pathlib.Path
    ) -> None:
        """Propagation: the two-branch flowchart must name cog (update-readme path)
        and make setup-ci / make test (ci path). Renames in either workflow
        surface as a red test."""
        readme = (baked / "README.md").read_text()
        mermaid = mermaid_block(readme)
        assert "make setup-ci" in mermaid
        assert "make test" in mermaid
        assert "cog" in mermaid


# ---------------------------------------------------------------------------
# No-workflow-only tests
# ---------------------------------------------------------------------------


class TestBakeWithoutWorkflow:
    """Tests specific to include_github_workflows='no'."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return _bake(tmp_path_factory.mktemp("no-workflow"), workflow="no")

    def test_no_github_directory(self, baked: pathlib.Path) -> None:
        assert not (baked / ".github").exists()

    def test_readme_has_no_ci_section(self, baked: pathlib.Path) -> None:
        """When the flag is no, the CI section must not leak into the README."""
        readme = (baked / "README.md").read_text()
        assert "## CI" not in readme
