"""Textual TUI dashboard for {{cookiecutter.project_name}}.

This module provides a minimal Textual application and the Click command
that ``{{cookiecutter.package_name}}.tui.cli`` registers onto the root CLI.
"""

from __future__ import annotations

import click
from pydantic import BaseModel
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static

APP_TITLE: str = "{{cookiecutter.project_name}}"
APP_SUBTITLE: str = "v0.1.0"
WELCOME_MESSAGE: str = "Welcome to {{cookiecutter.project_name}}. Press Q to quit."


class DashboardConfig(BaseModel):
    """Configuration for the Textual dashboard application."""

    title: str = APP_TITLE
    subtitle: str = APP_SUBTITLE
    message: str = WELCOME_MESSAGE


class DashboardApp(App[None]):
    """A minimal Textual application for {{cookiecutter.project_name}}."""

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, config: DashboardConfig | None = None) -> None:
        self._config = config or DashboardConfig()
        super().__init__()
        self.title = self._config.title
        self.sub_title = self._config.subtitle

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Static(self._config.message, id="welcome")
        yield Footer()


def create_app(config: DashboardConfig | None = None) -> DashboardApp:
    """Create and return a configured DashboardApp instance."""
    return DashboardApp(config=config)


# ---------------------------------------------------------------------------
# Click command — registered onto the root CLI by {{cookiecutter.package_name}}.tui.cli
# ---------------------------------------------------------------------------


@click.command()
def dashboard() -> None:
    """Launch the interactive dashboard TUI."""
    app = create_app()
    app.run()
