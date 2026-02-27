"""Tests for the {{cookiecutter.target_repo}} status subcommand."""

from io import StringIO

import click
import pytest
from click.testing import CliRunner
from rich.console import Console

from {{cookiecutter.package_name}}.tui.cli import cli
from {{cookiecutter.package_name}}.tui.status import (
    PROJECT_NAME,
    VERSION,
    StatusItem,
    StatusReport,
    get_status,
    render_status,
    status,
)


class TestConstants:
    """Tests for the status module constants."""

    def test_project_name_is_nonempty(self) -> None:
        assert len(PROJECT_NAME) > 0

    def test_version_is_nonempty(self) -> None:
        assert len(VERSION) > 0


class TestStatusItemModel:
    """Tests for the Pydantic StatusItem model."""

    def test_status_item_creation(self) -> None:
        item = StatusItem(label="Key", value="Val")
        assert item.label == "Key"
        assert item.value == "Val"

    def test_status_item_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            StatusItem()  # type: ignore[call-arg]


class TestStatusReportModel:
    """Tests for the Pydantic StatusReport model."""

    def test_status_report_creation(self) -> None:
        report = StatusReport(
            project="Test",
            version="1.0",
            items=[StatusItem(label="A", value="B")],
        )
        assert report.project == "Test"
        assert report.version == "1.0"
        assert len(report.items) == 1

    def test_status_report_requires_all_fields(self) -> None:
        with pytest.raises(Exception):
            StatusReport()  # type: ignore[call-arg]

    def test_status_report_empty_items(self) -> None:
        report = StatusReport(project="Test", version="1.0", items=[])
        assert report.items == []


class TestGetStatus:
    """Tests for the get_status function."""

    def test_returns_status_report(self) -> None:
        result = get_status()
        assert isinstance(result, StatusReport)

    def test_report_project_matches_constant(self) -> None:
        result = get_status()
        assert result.project == PROJECT_NAME

    def test_report_version_matches_constant(self) -> None:
        result = get_status()
        assert result.version == VERSION

    def test_report_has_items(self) -> None:
        result = get_status()
        assert len(result.items) > 0

    def test_report_items_are_status_items(self) -> None:
        result = get_status()
        for item in result.items:
            assert isinstance(item, StatusItem)


class TestRenderStatus:
    """Tests for the render_status function."""

    def test_render_produces_output(self) -> None:
        report = get_status()
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_status(report, console=console)
        output = buf.getvalue()
        assert len(output) > 0

    def test_render_contains_project_name(self) -> None:
        report = get_status()
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        render_status(report, console=console)
        output = buf.getvalue()
        assert PROJECT_NAME in output

    def test_render_returns_console(self) -> None:
        report = get_status()
        buf = StringIO()
        console = Console(file=buf, force_terminal=True)
        result = render_status(report, console=console)
        assert result is console

    def test_render_creates_console_when_none(self) -> None:
        report = get_status()
        result = render_status(report)
        assert isinstance(result, Console)


class TestStatusCLI:
    """Tests for the {{cookiecutter.target_repo}} status CLI command."""

    def test_status_exits_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_status_produces_output(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["status"])
        assert len(result.output) > 0


class TestStatusModuleStructure:
    """Tests that the status module is self-contained."""

    def test_status_is_click_command(self) -> None:
        assert isinstance(status, click.Command)

    def test_status_registered_on_cli(self) -> None:
        assert "status" in cli.commands
        assert cli.commands["status"] is status
