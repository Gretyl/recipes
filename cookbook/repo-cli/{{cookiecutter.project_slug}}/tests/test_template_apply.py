"""Tests for the {{cookiecutter.target_repo}} template apply subcommand."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from {{cookiecutter.package_name}}.tui.cli import cli
from {{cookiecutter.package_name}}.tui.template import (
    TEMPLATE_CODE,
    ApplyResult,
    apply_template,
    wrap_with_cog,
)


class TestWrapWithCog:
    """Tests for wrapping template code with Cog markers."""

    def test_wrap_includes_cog_open(self) -> None:
        result = wrap_with_cog("print('hello')")
        assert result.startswith("<!--[[[cog\n")

    def test_wrap_includes_cog_close(self) -> None:
        result = wrap_with_cog("print('hello')")
        assert "]]]-->" in result

    def test_wrap_includes_cog_end(self) -> None:
        result = wrap_with_cog("print('hello')")
        assert result.endswith("<!--[[[end]]]-->")

    def test_wrap_preserves_code(self) -> None:
        code = "import pathlib\nprint('hello')"
        result = wrap_with_cog(code)
        assert code in result

    def test_wrap_full_structure(self) -> None:
        code = "print('hello')"
        result = wrap_with_cog(code)
        expected = "<!--[[[cog\nprint('hello')\n]]]-->\n<!--[[[end]]]-->"
        assert result == expected

    def test_wrap_with_template_code(self) -> None:
        result = wrap_with_cog(TEMPLATE_CODE)
        assert result.startswith("<!--[[[cog\n")
        assert result.endswith("<!--[[[end]]]-->")
        assert TEMPLATE_CODE in result

    def test_wrap_with_noop_produces_valid_cog_block(self) -> None:
        """The wrapped stub should be a valid Cog block that produces no output."""
        result = wrap_with_cog(TEMPLATE_CODE)
        assert result == f"<!--[[[cog\n{TEMPLATE_CODE}\n]]]-->\n<!--[[[end]]]-->"


class TestApplyResultModel:
    """Tests for the Pydantic ApplyResult model."""

    def test_apply_result_creation(self) -> None:
        result = ApplyResult(
            readme_path="/some/path/README.md",
            placeholder_found=True,
            content_written=True,
        )
        assert result.readme_path == "/some/path/README.md"
        assert result.placeholder_found is True
        assert result.content_written is True

    def test_apply_result_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            ApplyResult()  # type: ignore[call-arg]


class TestApplyTemplate:
    """Tests for the apply_template function."""

    def test_replaces_placeholder_in_readme(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\n<template placeholder>\n\n## Footer\n")
        result = apply_template(readme)
        assert result.placeholder_found is True
        assert result.content_written is True
        content = readme.read_text()
        assert "<!--[[[cog" in content
        assert "<!--[[[end]]]-->" in content
        assert TEMPLATE_CODE in content
        assert "<template placeholder>" not in content

    def test_replaces_last_occurrence(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(
            "First: <template placeholder>\n\n"
            "Second: <template placeholder>\n"
        )
        result = apply_template(readme)
        assert result.placeholder_found is True
        content = readme.read_text()
        # The first occurrence should remain
        assert content.startswith("First: <template placeholder>")
        # The second should be replaced
        assert "Second: <!--[[[cog" in content

    def test_error_when_no_placeholder(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\nNo placeholder here\n")
        result = apply_template(readme)
        assert result.placeholder_found is False
        assert result.content_written is False

    def test_preserves_surrounding_content(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        header = "# My Repo\n\nSome intro text.\n\n"
        footer = "\n\n## Footer section\n\nMore text.\n"
        readme.write_text(header + "<template placeholder>" + footer)
        apply_template(readme)
        content = readme.read_text()
        assert content.startswith(header)
        assert content.endswith(footer)

    def test_apply_result_contains_path(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("<template placeholder>\n")
        result = apply_template(readme)
        assert result.readme_path == str(readme)

    def test_applied_cog_block_is_noop(self, tmp_path: Path) -> None:
        """After applying, the Cog block should contain the stub template code."""
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\n<template placeholder>\n")
        apply_template(readme)
        content = readme.read_text()
        assert f"<!--[[[cog\n{TEMPLATE_CODE}\n]]]-->" in content


class TestApplyCLI:
    """Tests for the {{cookiecutter.target_repo}} template apply CLI command."""

    def test_apply_replaces_placeholder(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\n<template placeholder>\n\n## Footer\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "apply", "--readme", str(readme)])
        assert result.exit_code == 0
        content = readme.read_text()
        assert "<!--[[[cog" in content
        assert TEMPLATE_CODE in content
        assert "<template placeholder>" not in content

    def test_apply_reports_missing_placeholder(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\nNo placeholder\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["template", "apply", "--readme", str(readme)])
        assert result.exit_code != 0

    def test_apply_default_readme_path(self) -> None:
        """Test that --readme defaults to README.md in current directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("README.md").write_text("<template placeholder>\n")
            result = runner.invoke(cli, ["template", "apply"])
            assert result.exit_code == 0
            content = Path("README.md").read_text()
            assert "<!--[[[cog" in content

    def test_apply_reports_missing_readme(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["template", "apply"])
            assert result.exit_code != 0
            assert "README not found" in result.output
