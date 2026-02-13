"""Tests for the {{cookiecutter.target_repo}} template prepare subcommand."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from {{cookiecutter.package_name}}.tui.cli import cli
from {{cookiecutter.package_name}}.tui.template import (
    COG_CLOSE,
    COG_END,
    COG_OPEN,
    PLACEHOLDER,
    TEMPLATE_CODE,
    PrepareResult,
    apply_template,
    prepare_template,
    wrap_with_cog,
)


class TestPrepareResultModel:
    """Tests for the Pydantic PrepareResult model."""

    def test_prepare_result_creation(self) -> None:
        result = PrepareResult(
            readme_path="/some/path/README.md",
            cog_block_found=True,
            placeholder_written=True,
        )
        assert result.readme_path == "/some/path/README.md"
        assert result.cog_block_found is True
        assert result.placeholder_written is True

    def test_prepare_result_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            PrepareResult()  # type: ignore[call-arg]


class TestPrepareTemplate:
    """Tests for the prepare_template function."""

    def test_replaces_cog_block_without_output(self, tmp_path: Path) -> None:
        """A Cog block with no cached output is replaced with the placeholder."""
        readme = tmp_path / "README.md"
        wrapped = wrap_with_cog(TEMPLATE_CODE)
        readme.write_text(f"# Title\n\n{wrapped}\n\n## Footer\n")
        result = prepare_template(readme)
        assert result.cog_block_found is True
        assert result.placeholder_written is True
        content = readme.read_text()
        assert PLACEHOLDER in content
        assert COG_OPEN not in content
        assert COG_END not in content

    def test_replaces_cog_block_with_cached_output(self, tmp_path: Path) -> None:
        """A Cog block with cached output between ]]]-- > and end marker is fully replaced."""
        readme = tmp_path / "README.md"
        cog_block = (
            f"{COG_OPEN}\n{TEMPLATE_CODE}\n{COG_CLOSE}\n"
            "Some cached output\nMore output\n"
            f"{COG_END}"
        )
        readme.write_text(f"# Title\n\n{cog_block}\n\n## Footer\n")
        result = prepare_template(readme)
        assert result.cog_block_found is True
        assert result.placeholder_written is True
        content = readme.read_text()
        assert PLACEHOLDER in content
        assert COG_OPEN not in content
        assert COG_END not in content
        assert "Some cached output" not in content

    def test_replaces_last_cog_block(self, tmp_path: Path) -> None:
        """When multiple Cog blocks exist, only the last is replaced."""
        readme = tmp_path / "README.md"
        first_block = f"{COG_OPEN}\nprint('first')\n{COG_CLOSE}\n{COG_END}"
        second_block = wrap_with_cog(TEMPLATE_CODE)
        readme.write_text(f"First: {first_block}\n\nSecond: {second_block}\n")
        result = prepare_template(readme)
        assert result.cog_block_found is True
        content = readme.read_text()
        # The first Cog block should remain
        assert f"First: {first_block}" in content
        # The second should be replaced with placeholder
        assert f"Second: {PLACEHOLDER}" in content

    def test_error_when_no_cog_block(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\nNo cog block here\n")
        result = prepare_template(readme)
        assert result.cog_block_found is False
        assert result.placeholder_written is False

    def test_preserves_surrounding_content(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        header = "# My Repo\n\nSome intro text.\n\n"
        footer = "\n\n## Footer section\n\nMore text.\n"
        wrapped = wrap_with_cog(TEMPLATE_CODE)
        readme.write_text(header + wrapped + footer)
        prepare_template(readme)
        content = readme.read_text()
        assert content.startswith(header)
        assert content.endswith(footer)

    def test_prepare_result_contains_path(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text(wrap_with_cog(TEMPLATE_CODE))
        result = prepare_template(readme)
        assert result.readme_path == str(readme)

    def test_prepared_noop_block_restores_placeholder(self, tmp_path: Path) -> None:
        """The no-op Cog block (pass) is correctly replaced with placeholder."""
        readme = tmp_path / "README.md"
        readme.write_text("<!--[[[cog\npass\n]]]-->\n<!--[[[end]]]-->")
        result = prepare_template(readme)
        assert result.cog_block_found is True
        assert readme.read_text() == PLACEHOLDER


class TestPrepareIdempotence:
    """Tests that apply and prepare are inverses of each other."""

    def test_apply_then_prepare_roundtrip(self, tmp_path: Path) -> None:
        """apply followed by prepare restores the placeholder."""
        readme = tmp_path / "README.md"
        original = f"# Title\n\n{PLACEHOLDER}\n\n## Footer\n"
        readme.write_text(original)
        apply_template(readme)
        # Confirm apply worked
        assert PLACEHOLDER not in readme.read_text()
        prepare_template(readme)
        assert readme.read_text() == original

    def test_prepare_then_apply_roundtrip(self, tmp_path: Path) -> None:
        """prepare followed by apply restores the Cog block."""
        readme = tmp_path / "README.md"
        wrapped = wrap_with_cog(TEMPLATE_CODE)
        original = f"# Title\n\n{wrapped}\n\n## Footer\n"
        readme.write_text(original)
        prepare_template(readme)
        # Confirm prepare worked
        assert COG_OPEN not in readme.read_text()
        apply_template(readme)
        assert readme.read_text() == original

    def test_apply_then_prepare_with_cached_output(self, tmp_path: Path) -> None:
        """prepare strips Cog-cached output, restoring placeholder even after Cog has run."""
        readme = tmp_path / "README.md"
        header = "# Title\n\n"
        footer = "\n\n## Footer\n"
        # Simulate what Cog produces: code block + generated output
        cog_with_output = (
            f"{COG_OPEN}\n{TEMPLATE_CODE}\n{COG_CLOSE}\n"
            "Generated content here\n"
            f"{COG_END}"
        )
        readme.write_text(header + cog_with_output + footer)
        prepare_template(readme)
        assert readme.read_text() == header + PLACEHOLDER + footer

    def test_double_prepare_is_noop(self, tmp_path: Path) -> None:
        """Running prepare twice: first succeeds, second reports no cog block."""
        readme = tmp_path / "README.md"
        readme.write_text(wrap_with_cog(TEMPLATE_CODE))
        first = prepare_template(readme)
        assert first.cog_block_found is True
        second = prepare_template(readme)
        assert second.cog_block_found is False

    def test_double_apply_then_prepare(self, tmp_path: Path) -> None:
        """apply is already idempotent (no placeholder after first apply), prepare still works."""
        readme = tmp_path / "README.md"
        original = f"{PLACEHOLDER}\n"
        readme.write_text(original)
        apply_template(readme)
        # Second apply finds no placeholder — no-op
        second_apply = apply_template(readme)
        assert second_apply.placeholder_found is False
        # prepare still restores
        prepare_template(readme)
        assert readme.read_text() == original


class TestPrepareCLI:
    """Tests for the {{cookiecutter.target_repo}} template prepare CLI command."""

    def test_prepare_replaces_cog_block(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        wrapped = wrap_with_cog(TEMPLATE_CODE)
        readme.write_text(f"# Title\n\n{wrapped}\n\n## Footer\n")
        runner = CliRunner()
        result = runner.invoke(
            cli, ["template", "prepare", "--readme", str(readme)]
        )
        assert result.exit_code == 0
        content = readme.read_text()
        assert PLACEHOLDER in content
        assert COG_OPEN not in content

    def test_prepare_reports_missing_cog_block(self, tmp_path: Path) -> None:
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\nNo cog block\n")
        runner = CliRunner()
        result = runner.invoke(
            cli, ["template", "prepare", "--readme", str(readme)]
        )
        assert result.exit_code != 0

    def test_prepare_default_readme_path(self) -> None:
        """Test that --readme defaults to README.md in current directory."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("README.md").write_text(wrap_with_cog(TEMPLATE_CODE) + "\n")
            result = runner.invoke(cli, ["template", "prepare"])
            assert result.exit_code == 0
            content = Path("README.md").read_text()
            assert PLACEHOLDER in content

    def test_prepare_reports_missing_readme(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["template", "prepare"])
            assert result.exit_code != 0
            assert "README not found" in result.output

    def test_prepare_with_cached_output_via_cli(self, tmp_path: Path) -> None:
        """CLI handles Cog blocks that include cached output."""
        readme = tmp_path / "README.md"
        cog_block = (
            f"{COG_OPEN}\n{TEMPLATE_CODE}\n{COG_CLOSE}\n"
            "cached output here\n"
            f"{COG_END}"
        )
        readme.write_text(cog_block)
        runner = CliRunner()
        result = runner.invoke(
            cli, ["template", "prepare", "--readme", str(readme)]
        )
        assert result.exit_code == 0
        content = readme.read_text()
        assert PLACEHOLDER in content
        assert "cached output" not in content
