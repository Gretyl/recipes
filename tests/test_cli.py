from click.testing import CliRunner

from recipes_cli.tui.cli import cli


def test_hello_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello from recipes_cli.tui" in result.output


def test_no_args_shows_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output
    assert "hello" in result.output
    assert "help" in result.output


def test_help_subcommand() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output
    assert "hello" in result.output


def test_help_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output


def test_commands_listed_alphabetically() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    commands_section = result.output[result.output.index("Commands:") :]
    hello_pos = commands_section.index("hello")
    help_pos = commands_section.index("help", hello_pos + 1)
    assert hello_pos < help_pos
