"""Bake-level tests for the repo-cli cookiecutter template.

These tests programmatically run cookiecutter against the template
with both values of ``include_github_workflows`` and verify the
resulting file trees and file contents.
"""

import pathlib
import subprocess

import pytest

from tests.helpers import (
    bake,
    find_jinja_leaks,
    makefile_recipe,
    mermaid_block,
    paths,
)


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


def test_does_not_ship_claude_md(baked: pathlib.Path) -> None:
    """`repo-cli` is designed to bake into a host repo as a subpackage. The
    host already owns the project-root `CLAUDE.md`; shipping one with the
    template would either duplicate or shadow it. Agents reach the CLI's
    AGENTS.md by navigating into `{{package_name}}/`."""
    assert not (baked / "CLAUDE.md").exists()


def test_agents_md_pr_convention_is_narrative(baked: pathlib.Path) -> None:
    """Baked AGENTS.md must mirror the parent repo's narrative-PR-body
    convention. The earlier "List all commits in-order as the PR body"
    wording contradicted /AGENTS.md and is forbidden."""
    agents = (baked / "demo_repo_cli" / "AGENTS.md").read_text()
    assert "List all commits in-order as the PR body" not in agents
    assert "narrative" in agents.lower()
    assert "not a commit list" in agents.lower()


def test_agents_md_documents_conventional_commits(baked: pathlib.Path) -> None:
    """Baked AGENTS.md must name the Conventional Commits convention and list
    the parent repo's allowed types so a fresh punch doesn't have to chase
    the convention upstream."""
    agents = (baked / "demo_repo_cli" / "AGENTS.md").read_text()
    assert "Conventional Commits" in agents
    for commit_type in ("feat", "fix", "test", "docs", "chore", "refactor"):
        assert f"`{commit_type}`" in agents, (
            f"AGENTS.md must list {commit_type!r} as a commit type"
        )


def test_agents_md_documents_cog_block_etiquette(baked: pathlib.Path) -> None:
    """Baked AGENTS.md must warn that edits inside README.md's Cog blocks are
    overwritten on every push by `update-readme.yml`. Names the COG_OPEN
    delimiter so an agent searching the docs finds the section, and points
    at `template.py` as the canonical edit site."""
    agents = (baked / "demo_repo_cli" / "AGENTS.md").read_text()
    assert "Cog" in agents
    assert "[[[cog" in agents
    assert "template.py" in agents


def test_no_raw_template_variables(baked: pathlib.Path) -> None:
    """No file should contain un-rendered cookiecutter variables."""
    offenders = find_jinja_leaks(baked, require_cookiecutter=True)
    assert not offenders, f"un-rendered template variables remain in: {offenders}"


def test_cli_defines_ordered_group_with_alphabetical_override(
    baked: pathlib.Path,
) -> None:
    """The CLI's signature behaviour: subcommand listings sort
    alphabetically regardless of registration order. The notes call
    `OrderedGroup` out as the seam — without it, `cli.add_command(...)`
    order leaks into `--help` output and dashboards-before-status
    becomes a maintenance ordering problem rather than a code property.

    Pin three things:
    1. The class exists with the canonical name (so the import in
       AGENTS.md stays accurate).
    2. It overrides `list_commands` with a `sorted(super().list_commands(...))`
       call (the one-line idiom is what makes the property a property).
    3. The Click group is wired with `cls=OrderedGroup` (otherwise the
       override never fires)."""
    cli_py = (baked / "demo_repo_cli" / "tui" / "cli.py").read_text()
    assert "class OrderedGroup(click.Group):" in cli_py, (
        "cli.py must define `class OrderedGroup(click.Group)` — the "
        "alphabetical-listing seam"
    )
    assert "def list_commands(" in cli_py, (
        "OrderedGroup must override `list_commands` — without the override, "
        "Click falls back to insertion order"
    )
    assert "sorted(super().list_commands(" in cli_py, (
        "the override must call `sorted(super().list_commands(ctx))` — "
        "any other body silently changes the contract"
    )
    assert "cls=OrderedGroup" in cli_py, (
        "@click.group must be decorated with `cls=OrderedGroup` — without "
        "it the class exists but never fires"
    )


def test_baked_agents_md_documents_cli_scope_and_standards(
    baked: pathlib.Path,
) -> None:
    """The baked package's AGENTS.md replaces the older `CLI.md` scope
    document — it's where every author of a baked CLI looks for the
    development standards before adding a subcommand. Pin the four
    durable claims the cookbook notes promise are there:

    1. **Scope** — programmatic project support, not application logic.
    2. **OrderedGroup** entry-point architecture.
    3. **Pydantic** for structured-data inputs/outputs.
    4. **TDD discipline** — red/green pairs are mandatory.

    Without these, a baked CLI inherits the directory layout but loses
    the conventions that distinguish `repo-cli` from a generic Click
    boilerplate."""
    agents = (baked / "demo_repo_cli" / "AGENTS.md").read_text()
    assert "## Scope" in agents, (
        "AGENTS.md must declare a `## Scope` section — the boundary "
        "between project-support tooling and application code"
    )
    assert "project support" in agents.lower(), (
        "the Scope section must name the CLI's role as project support "
        "tooling, not just describe the layout"
    )
    assert "OrderedGroup" in agents, (
        "AGENTS.md must reference `OrderedGroup` — every author needs to "
        "know what wires the alphabetical listing"
    )
    assert "Pydantic" in agents, (
        "the development-standards section must name Pydantic for "
        "structured-data signatures"
    )
    assert "red/green" in agents.lower() or "red-green" in agents.lower(), (
        "the development-standards section must name red/green TDD as "
        "the discipline for adding subcommands"
    )
    assert "mypy" in agents.lower(), (
        "the development-standards section must require strict mypy"
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
    assert "CLAUDE.md" not in tree
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
