"""Tests for the {{cookiecutter.target_repo}} template subcommand."""

import click
import pytest
from click.testing import CliRunner

from {{cookiecutter.package_name}}.tui.cli import cli
from {{cookiecutter.package_name}}.tui.template import (
    COG_CLOSE,
    COG_END,
    COG_OPEN,
    TEMPLATE_CODE,
    TemplateOutput,
    get_template_code,
    template,
)


class TestTemplateCode:
    """Tests for the template code constant."""

    def test_template_code_is_nonempty(self) -> None:
        assert len(TEMPLATE_CODE) > 0

    def test_template_code_is_valid_python(self) -> None:
        """The stub template code must be executable Python."""
        compile(TEMPLATE_CODE, "<template>", "exec")

    def test_template_code_is_noop(self) -> None:
        """The stub template should produce no output when executed."""
        from io import StringIO
        import contextlib

        f = StringIO()
        with contextlib.redirect_stdout(f):
            exec(TEMPLATE_CODE)  # noqa: S102
        assert f.getvalue() == ""

    def test_template_code_does_not_contain_cog_markers(self) -> None:
        assert "<!--[[[cog" not in TEMPLATE_CODE
        assert "]]]-->" not in TEMPLATE_CODE
        assert "<!--[[[end]]]-->" not in TEMPLATE_CODE


class TestTemplateOutputModel:
    """Tests for the Pydantic TemplateOutput model."""

    def test_template_output_creation(self) -> None:
        output = TemplateOutput(code="print('hello')")
        assert output.code == "print('hello')"

    def test_template_output_requires_code(self) -> None:
        with pytest.raises(Exception):
            TemplateOutput()  # type: ignore[call-arg]


class TestGetTemplateCode:
    """Tests for the get_template_code function."""

    def test_returns_template_output(self) -> None:
        result = get_template_code()
        assert isinstance(result, TemplateOutput)

    def test_returns_nonempty_code(self) -> None:
        result = get_template_code()
        assert len(result.code) > 0

    def test_code_matches_constant(self) -> None:
        result = get_template_code()
        assert result.code == TEMPLATE_CODE


class TestCogMarkers:
    """Tests for the Cog marker constants."""

    def test_cog_open(self) -> None:
        assert COG_OPEN == "<!--[[[cog"

    def test_cog_close(self) -> None:
        assert COG_CLOSE == "]]]-->"

    def test_cog_end(self) -> None:
        assert COG_END == "<!--[[[end]]]-->"


class TestTemplateCLI:
    """Tests for the {{cookiecutter.target_repo}} template CLI command."""

    def test_template_outputs_code(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["template"])
        assert result.exit_code == 0
        assert TEMPLATE_CODE in result.output

    def test_template_output_does_not_contain_cog_markers(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["template"])
        assert result.exit_code == 0
        assert "<!--[[[cog" not in result.output
        assert "<!--[[[end]]]-->" not in result.output

    def test_template_output_matches_constant(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["template"])
        assert result.exit_code == 0
        # Output has trailing newline from click.echo
        assert result.output.strip() == TEMPLATE_CODE


class TestTemplateModuleStructure:
    """Tests that the template module is self-contained."""

    def test_template_group_is_click_group(self) -> None:
        assert isinstance(template, click.Group)

    def test_template_group_has_apply_subcommand(self) -> None:
        assert "apply" in template.commands

    def test_template_group_has_prepare_subcommand(self) -> None:
        assert "prepare" in template.commands

    def test_template_group_registered_on_cli(self) -> None:
        assert "template" in cli.commands
        assert cli.commands["template"] is template
