"""Round 2: pin the source-passage skeleton produced by a default bake.

A default-answer bake must yield exactly these six Twee 3 source
passages under `src/`, all rendered (no surviving `{{` markers).
This is the round that establishes that
`template/{{cookiecutter.project_slug}}/` exists at all and that the
six files it contains are syntactically clean Twee.

Build-harness files (Makefile, pyproject.toml, install-tweego.sh,
tests/test_smoke.py) are pinned in round 3.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def baked_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output_dir = tmp_path_factory.mktemp("bake-default")
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(output_dir),
    )
    project = output_dir / "my-narrative"
    assert project.is_dir(), f"bake did not create {project}"
    return project


REQUIRED_SOURCE_PASSAGES = [
    "src/StoryData.twee",
    "src/StoryTitle.twee",
    "src/StoryStylesheet.twee",
    "src/StoryScript.twee",
    "src/StoryInit.twee",
    "src/Start.twee",
]


@pytest.mark.parametrize("relpath", REQUIRED_SOURCE_PASSAGES)
def test_source_passage_exists(baked_project: Path, relpath: str) -> None:
    target = baked_project / relpath
    assert target.is_file(), f"missing required source passage: {relpath}"
    assert target.read_text().strip(), f"source passage {relpath} is empty"


def test_storydata_declares_passage_header(baked_project: Path) -> None:
    """Twee 3 special passages start with `:: StoryData`."""
    content = (baked_project / "src/StoryData.twee").read_text()
    assert content.lstrip().startswith(":: StoryData"), (
        "StoryData.twee must begin with `:: StoryData` Twee 3 header"
    )


def test_start_passage_header(baked_project: Path) -> None:
    """The Start passage is the entry point; SugarCube/Harlowe both expect it."""
    content = (baked_project / "src/Start.twee").read_text()
    assert content.lstrip().startswith(":: Start"), (
        "Start.twee must begin with `:: Start` Twee 3 header"
    )


def test_no_unrendered_jinja_markers_anywhere(baked_project: Path) -> None:
    """If any baked file contains `{{` or `}}`, cookiecutter rendering broke.

    Twee/SugarCube/Harlowe/Chapbook/Snowman use `<<…>>` and `[[…]]`,
    never `{{…}}`. JSON uses single `{` and `}`. So a stray double brace
    is unambiguously an unrendered Jinja2 token.
    """
    offenders: list[str] = []
    for path in baked_project.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        if "{{" in content or "}}" in content:
            offenders.append(str(path.relative_to(baked_project)))
    assert not offenders, f"unrendered Jinja2 markers in: {offenders}"
