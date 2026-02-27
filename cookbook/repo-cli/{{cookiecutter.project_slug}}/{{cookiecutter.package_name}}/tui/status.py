"""Project status display using Rich.

This module is the self-contained implementation of the
``{{cookiecutter.target_repo}} status`` subcommand.  It owns the Pydantic
models, business logic, and Click command that
``{{cookiecutter.package_name}}.tui.cli`` registers onto the root CLI.
"""

from __future__ import annotations

import click
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

PROJECT_NAME: str = "{{cookiecutter.project_name}}"
VERSION: str = "0.1.0"


class StatusItem(BaseModel):
    """A single key-value status entry."""

    label: str
    value: str


class StatusReport(BaseModel):
    """A collection of status items describing the project."""

    project: str
    version: str
    items: list[StatusItem]


def get_status() -> StatusReport:
    """Collect the current project status."""
    return StatusReport(
        project=PROJECT_NAME,
        version=VERSION,
        items=[
            StatusItem(label="Project", value=PROJECT_NAME),
            StatusItem(label="Version", value=VERSION),
            StatusItem(label="Status", value="OK"),
        ],
    )


def render_status(report: StatusReport, console: Console | None = None) -> Console:
    """Render a StatusReport as a Rich table.

    Returns the Console instance used (useful for testing with captured output).
    """
    if console is None:
        console = Console()
    table = Table(title=f"{report.project} Status")
    table.add_column("Property", style="bold")
    table.add_column("Value")
    for item in report.items:
        table.add_row(item.label, item.value)
    console.print(table)
    return console


# ---------------------------------------------------------------------------
# Click command — registered onto the root CLI by {{cookiecutter.package_name}}.tui.cli
# ---------------------------------------------------------------------------


@click.command()
def status() -> None:
    """Show project status using Rich formatting."""
    report = get_status()
    render_status(report)
