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
    assert "dashboard" in result.output
    assert "hello" in result.output
    assert "help" in result.output
    assert "status" in result.output
    assert "template" in result.output


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
    commands_section = result.output[result.output.index("Commands:") :]
    dashboard_pos = commands_section.index("dashboard")
    hello_pos = commands_section.index("hello")
    help_pos = commands_section.index("help", hello_pos + 1)
    status_pos = commands_section.index("status")
    template_pos = commands_section.index("template")
    assert dashboard_pos < hello_pos < help_pos < status_pos < template_pos
