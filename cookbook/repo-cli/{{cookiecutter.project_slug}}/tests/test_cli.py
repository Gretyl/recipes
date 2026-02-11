from click.testing import CliRunner

from {{cookiecutter.package_name}}.tui.cli import cli


def test_hello_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello from {{cookiecutter.package_name}}.tui" in result.output
