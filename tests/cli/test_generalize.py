import json
from pathlib import Path

from click.testing import CliRunner

from recipes_cli.tui.cli import cli


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


def test_generalize_appears_in_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "generalize" in result.output


def test_generalize_requires_dst(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(cli, ["generalize", "--src", str(tmp_path)])
    assert result.exit_code != 0


def test_generalize_creates_template(runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

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


def test_generalize_templates_pyproject_toml(runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

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


def test_generalize_templates_readme_heading(runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code == 0

    readme = (
        dst / "cookiecutter-myproject" / "{{cookiecutter.project_slug}}" / "README.md"
    )
    content = readme.read_text()
    assert "{{cookiecutter.package_name}}" in content


def test_generalize_custom_template_name(runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

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


def test_generalize_src_defaults_to_cwd(runner: CliRunner, tmp_path: Path) -> None:
    """When --src is omitted, generalize should use the current directory."""
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()

    with runner.isolated_filesystem(temp_dir=repo) as td:
        result = runner.invoke(cli, ["generalize", "--dst", str(dst)])

    assert result.exit_code == 0
    assert (dst / f"cookiecutter-{Path(td).name}").is_dir()


def test_generalize_fails_if_template_exists(runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    dst = tmp_path / "output"
    dst.mkdir()
    # Pre-create the template folder to trigger the collision
    (dst / "cookiecutter-myproject").mkdir()

    result = runner.invoke(cli, ["generalize", "--src", str(repo), "--dst", str(dst)])
    assert result.exit_code != 0


def test_generalize_replaces_package_name_in_py_files(
    runner: CliRunner, tmp_path: Path
) -> None:
    repo = _make_fake_repo(tmp_path)
    # Add a file that references the package name
    (repo / "mypackage" / "core.py").write_text("from mypackage import something\n")
    dst = tmp_path / "output"
    dst.mkdir()

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
