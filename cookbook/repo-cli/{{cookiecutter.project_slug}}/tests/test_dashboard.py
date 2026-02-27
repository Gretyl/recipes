"""Tests for the {{cookiecutter.target_repo}} dashboard subcommand."""

import asyncio

import click
import pytest
from textual.widgets import Footer, Header, Static

from {{cookiecutter.package_name}}.tui.cli import cli
from {{cookiecutter.package_name}}.tui.dashboard import (
    APP_SUBTITLE,
    APP_TITLE,
    WELCOME_MESSAGE,
    DashboardApp,
    DashboardConfig,
    create_app,
    dashboard,
)


class TestConstants:
    """Tests for the dashboard module constants."""

    def test_app_title_is_nonempty(self) -> None:
        assert len(APP_TITLE) > 0

    def test_app_subtitle_is_nonempty(self) -> None:
        assert len(APP_SUBTITLE) > 0

    def test_welcome_message_is_nonempty(self) -> None:
        assert len(WELCOME_MESSAGE) > 0


class TestDashboardConfigModel:
    """Tests for the Pydantic DashboardConfig model."""

    def test_config_defaults(self) -> None:
        config = DashboardConfig()
        assert config.title == APP_TITLE
        assert config.subtitle == APP_SUBTITLE
        assert config.message == WELCOME_MESSAGE

    def test_config_custom_values(self) -> None:
        config = DashboardConfig(title="Custom", subtitle="v2.0", message="Hi")
        assert config.title == "Custom"
        assert config.subtitle == "v2.0"
        assert config.message == "Hi"


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_returns_dashboard_app(self) -> None:
        app = create_app()
        assert isinstance(app, DashboardApp)

    def test_default_config(self) -> None:
        app = create_app()
        assert app.title == APP_TITLE
        assert app.sub_title == APP_SUBTITLE

    def test_custom_config(self) -> None:
        config = DashboardConfig(title="Custom", subtitle="v2.0", message="Hi")
        app = create_app(config=config)
        assert app.title == "Custom"
        assert app.sub_title == "v2.0"


class TestDashboardApp:
    """Tests for the DashboardApp Textual application."""

    def test_app_is_textual_app(self) -> None:
        from textual.app import App

        assert issubclass(DashboardApp, App)

    def test_app_has_quit_binding(self) -> None:
        bindings = DashboardApp.BINDINGS
        keys = [b[0] if isinstance(b, tuple) else b.key for b in bindings]
        assert "q" in keys

    def test_app_composes_widgets(self) -> None:
        """Verify compose yields Header, Static, and Footer."""

        async def _check() -> None:
            app = create_app()
            async with app.run_test():
                app.query_one(Header)
                app.query_one(Footer)
                welcome = app.query_one("#welcome", Static)
                assert WELCOME_MESSAGE in welcome.content

        asyncio.run(_check())


class TestDashboardCommand:
    """Tests that the dashboard command is properly registered."""

    def test_dashboard_is_click_command(self) -> None:
        assert isinstance(dashboard, click.Command)

    def test_dashboard_registered_on_cli(self) -> None:
        assert "dashboard" in cli.commands
        assert cli.commands["dashboard"] is dashboard
