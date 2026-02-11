from click.testing import CliRunner

from {{cookiecutter.package_name}}.tui.cli import cli


def test_hello_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello from {{cookiecutter.package_name}}.tui" in result.output


def test_no_args_shows_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "{{cookiecutter.project_name}}" in result.output
    assert "hello" in result.output
    assert "help" in result.output


def test_help_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["help"])
    assert result.exit_code == 0
    assert "{{cookiecutter.project_name}}" in result.output
    assert "hello" in result.output


def test_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "{{cookiecutter.project_name}}" in result.output


def test_commands_listed_alphabetically() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    output = result.output
    hello_pos = output.index("hello")
    help_pos = output.index("help")
    assert hello_pos < help_pos
