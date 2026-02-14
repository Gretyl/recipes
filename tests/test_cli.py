import json
from pathlib import Path

from click.testing import CliRunner

from recipes_cli.tui.cli import cli


def test_no_args_shows_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output
    assert "help" in result.output


def test_help_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output


def test_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output


def test_commands_listed_alphabetically() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    commands_section = result.output[result.output.index("Commands:") :]
    generalize_pos = commands_section.index("generalize")
    help_pos = commands_section.index("help")
    meld_pos = commands_section.index("meld")
    assert generalize_pos < help_pos < meld_pos


# ---------------------------------------------------------------------------
# recipes generalize
# ---------------------------------------------------------------------------


def _make_fake_repo(base: Path) -> Path:
    """Create a minimal Python repo structure for generalize tests."""
    repo = base / "myproject"
    repo.mkdir()
    pkg = repo / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""My package."""\n')
    (pkg / "core.py").write_text("def run() -> None:\n    pass\n")
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "myproject"\ndescription = "A cool project"\n'
    )
    (repo / "README.md").write_text("# myproject\n\nA cool project.\n")
    return repo


def test_generalize_appears_in_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "generalize" in result.output


def test_generalize_requires_dst(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(tmp_path)])
    assert result.exit_code != 0


def test_generalize_creates_template(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code == 0

    # Template directory should exist
    template_root = dst / "cookiecutter-myproject"
    assert template_root.is_dir()

    # cookiecutter.json should have correct variables
    cc_json = json.loads((template_root / "cookiecutter.json").read_text())
    assert cc_json["project_slug"] == "myproject"
    assert cc_json["package_name"] == "mypackage"

    # Skeleton should use cookiecutter variable for package dir
    skeleton = template_root / "{{cookiecutter.project_slug}}"
    assert skeleton.is_dir()
    assert (skeleton / "{{cookiecutter.package_name}}").is_dir()
    assert (skeleton / "{{cookiecutter.package_name}}" / "__init__.py").exists()


def test_generalize_templates_pyproject_toml(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code == 0

    pyproject = (
        dst
        / "cookiecutter-myproject"
        / "{{cookiecutter.project_slug}}"
        / "pyproject.toml"
    )
    content = pyproject.read_text()
    assert "{{cookiecutter.project_slug}}" in content
    assert "{{cookiecutter.project_name}}" in content


def test_generalize_templates_readme_heading(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code == 0

    readme = (
        dst / "cookiecutter-myproject" / "{{cookiecutter.project_slug}}" / "README.md"
    )
    content = readme.read_text()
    assert "{{cookiecutter.package_name}}" in content


def test_generalize_custom_template_name(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "generalize",
            "--src",
            str(repo),
            "--dst",
            str(dst),
            "--template-name",
            "my-custom-template",
        ],
    )
    assert result.exit_code == 0
    assert (dst / "my-custom-template").is_dir()
    assert (dst / "my-custom-template" / "cookiecutter.json").exists()


def test_generalize_src_defaults_to_cwd(tmp_path: Path) -> None:
    """When --src is omitted, generalize should use the current directory."""
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=repo) as td:
        result = runner.invoke(cli, ["generalize", "--dst", str(dst)])

    assert result.exit_code == 0
    assert (dst / f"cookiecutter-{Path(td).name}").is_dir()


def test_generalize_fails_if_template_exists(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()
    # Pre-create the template folder to trigger the collision
    (dst / "cookiecutter-myproject").mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code != 0


def test_generalize_replaces_package_name_in_py_files(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    # Add a file that references the package name
    (repo / "mypackage" / "core.py").write_text("from mypackage import something\n")
    dst = tmp_path / "output"
    dst.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code == 0

    core_py = (
        dst
        / "cookiecutter-myproject"
        / "{{cookiecutter.project_slug}}"
        / "{{cookiecutter.package_name}}"
        / "core.py"
    )
    content = core_py.read_text()
    assert "{{cookiecutter.package_name}}" in content
    assert "mypackage" not in content


# ---------------------------------------------------------------------------
# recipes meld makefiles
# ---------------------------------------------------------------------------


_SOURCE_MAKEFILE = """\
.PHONY: test lint deploy

PYTHON := python3
DEPLOY_TARGET := production

test:
\t$(PYTHON) -m pytest

lint:
\t$(PYTHON) -m ruff check .

deploy:
\t./deploy.sh $(DEPLOY_TARGET)
"""

_TARGET_MAKEFILE = """\
.PHONY: test

PYTHON := python3

test:
\t$(PYTHON) -m pytest --cov
"""


def test_meld_group_appears_in_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "meld" in result.output


def test_meld_makefiles_appears_in_meld_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["meld", "--help"])
    assert result.exit_code == 0
    assert "makefiles" in result.output


def test_meld_makefiles_analysis_output(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt)])
    assert result.exit_code == 0
    # Should detect new targets
    assert "lint" in result.output
    assert "deploy" in result.output


def test_meld_makefiles_json_output(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tgt), "--output", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "lint" in data["new_targets"]
    assert "deploy" in data["new_targets"]


def test_meld_makefiles_detects_modified_target(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    # test target has different recipe in source vs target
    assert "test" in data["modified_targets"]


def test_meld_makefiles_detects_new_variables(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DEPLOY_TARGET" in data["new_variables"]


def test_meld_makefiles_diff_output(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "diff"])
    assert result.exit_code == 0
    assert "---" in result.output
    assert "+++" in result.output


def test_meld_makefiles_prompt_output(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tgt), "-o", "prompt"]
    )
    assert result.exit_code == 0
    assert "Analysis Request" in result.output


def test_meld_makefiles_nonexistent_source(tmp_path: Path) -> None:
    tgt = tmp_path / "target.mk"
    tgt.write_text(_TARGET_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["meld", "makefiles", str(tmp_path / "nope.mk"), str(tgt)]
    )
    assert result.exit_code != 0


def test_meld_makefiles_nonexistent_target(tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    src.write_text(_SOURCE_MAKEFILE)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tmp_path / "nope.mk")]
    )
    assert result.exit_code != 0
