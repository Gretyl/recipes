import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from recipes_cli.tui.cli import cli

_SOURCE_MAKEFILE = """\
.PHONY: test lint deploy

PYTHON := python3
DEPLOY_TARGET := production

test:
\t$(PYTHON) -m pytest

lint:
\t$(PYTHON) -m ruff check .

deploy:
\t./deploy.sh $(DEPLOY_TARGET)
"""

_TARGET_MAKEFILE = """\
.PHONY: test

PYTHON := python3

test:
\t$(PYTHON) -m pytest --cov
"""


@pytest.fixture()
def meld_makefiles(tmp_path: Path) -> tuple[Path, Path]:
    """Write the source and target Makefiles and return their paths."""
    src = tmp_path / "source.mk"
    tgt = tmp_path / "target.mk"
    src.write_text(_SOURCE_MAKEFILE)
    tgt.write_text(_TARGET_MAKEFILE)
    return src, tgt


def test_meld_group_appears_in_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "meld" in result.output


def test_meld_makefiles_appears_in_meld_help(runner: CliRunner) -> None:
    result = runner.invoke(cli, ["meld", "--help"])
    assert result.exit_code == 0
    assert "makefiles" in result.output


def test_meld_makefiles_analysis_output(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt)])
    assert result.exit_code == 0
    # Should detect new targets
    assert "lint" in result.output
    assert "deploy" in result.output


def test_meld_makefiles_json_output(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tgt), "--output", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "lint" in data["new_targets"]
    assert "deploy" in data["new_targets"]


def test_meld_makefiles_detects_modified_target(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    # test target has different recipe in source vs target
    assert "test" in data["modified_targets"]


def test_meld_makefiles_detects_new_variables(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "DEPLOY_TARGET" in data["new_variables"]


def test_meld_makefiles_diff_output(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(cli, ["meld", "makefiles", str(src), str(tgt), "-o", "diff"])
    assert result.exit_code == 0
    assert "---" in result.output
    assert "+++" in result.output


def test_meld_makefiles_prompt_output(
    runner: CliRunner, meld_makefiles: tuple[Path, Path]
) -> None:
    src, tgt = meld_makefiles
    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tgt), "-o", "prompt"]
    )
    assert result.exit_code == 0
    assert "Analysis Request" in result.output


def test_meld_makefiles_nonexistent_source(runner: CliRunner, tmp_path: Path) -> None:
    tgt = tmp_path / "target.mk"
    tgt.write_text(_TARGET_MAKEFILE)

    result = runner.invoke(
        cli, ["meld", "makefiles", str(tmp_path / "nope.mk"), str(tgt)]
    )
    assert result.exit_code != 0


def test_meld_makefiles_nonexistent_target(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "source.mk"
    src.write_text(_SOURCE_MAKEFILE)

    result = runner.invoke(
        cli, ["meld", "makefiles", str(src), str(tmp_path / "nope.mk")]
    )
    assert result.exit_code != 0
