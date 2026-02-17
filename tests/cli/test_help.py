from click.testing import CliRunner

from recipes_cli.tui.cli import cli


def test_no_args_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output
    assert "help" in result.output


def test_help_subcommand(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output


def test_help_flag(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Recipes CLI" in result.output


def test_commands_listed_alphabetically(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    commands_section = result.output[result.output.index("Commands:") :]
    generalize_pos = commands_section.index("generalize")
    help_pos = commands_section.index("help")
    meld_pos = commands_section.index("meld")
    assert generalize_pos < help_pos < meld_pos
