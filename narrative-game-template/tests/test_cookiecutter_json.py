"""Round 1: pin the shape of `template/cookiecutter.json`.

Failing-by-construction without an implementation: the JSON file does
not yet exist. Even once it exists, weakening any one of the assertions
below (typo'd key, wrong default, missing story format) fails the
suite — so this test cannot be satisfied by an empty stub.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

TEMPLATE_DIR = Path(__file__).parent.parent
COOKIECUTTER_JSON = TEMPLATE_DIR / "cookiecutter.json"

# The four official Twine 2 story formats bundled with tweego.
# Paperthin is excluded — it's a story-format-authoring format, not a
# game-shipping format.
TWEEGO_BUNDLED_FORMATS = {"sugarcube", "harlowe", "chapbook", "snowman"}


@pytest.fixture(scope="module")
def cookiecutter_config() -> dict:
    assert COOKIECUTTER_JSON.is_file(), (
        f"expected cookiecutter.json at {COOKIECUTTER_JSON}, but it does not exist"
    )
    return json.loads(COOKIECUTTER_JSON.read_text())


def test_exposes_six_documented_prompts(cookiecutter_config: dict) -> None:
    """The 6 prompts in the design doc are all present, no extras."""
    expected_keys = {
        "project_slug",
        "title",
        "author_name",
        "story_format",
        "ifid",
        "include_github_workflow",
    }
    actual_keys = {k for k in cookiecutter_config if not k.startswith("_")}
    assert actual_keys == expected_keys, (
        f"prompts mismatch: missing={expected_keys - actual_keys}, "
        f"unexpected={actual_keys - expected_keys}"
    )


def test_default_project_slug(cookiecutter_config: dict) -> None:
    assert cookiecutter_config["project_slug"] == "my-narrative"


def test_default_title(cookiecutter_config: dict) -> None:
    assert cookiecutter_config["title"] == "An Untitled Room"


def test_default_author_name(cookiecutter_config: dict) -> None:
    assert cookiecutter_config["author_name"] == "Anonymous"


def test_default_ifid_is_empty_for_runtime_synthesis(cookiecutter_config: dict) -> None:
    """An empty IFID signals pre_gen_project to mint a fresh UUID4."""
    assert cookiecutter_config["ifid"] == ""


def test_story_format_choices_match_tweego_bundled(cookiecutter_config: dict) -> None:
    """story_format is a list of exactly the 4 tweego-bundled formats."""
    formats = cookiecutter_config["story_format"]
    assert isinstance(formats, list), "story_format must be a list (cookiecutter choice prompt)"
    assert len(formats) == 4, f"expected 4 story formats, got {len(formats)}: {formats}"
    assert set(formats) == TWEEGO_BUNDLED_FORMATS, (
        f"story_format set mismatch: missing={TWEEGO_BUNDLED_FORMATS - set(formats)}, "
        f"unexpected={set(formats) - TWEEGO_BUNDLED_FORMATS}"
    )


def test_story_format_default_is_sugarcube(cookiecutter_config: dict) -> None:
    """First element of a cookiecutter choice list is the default."""
    assert cookiecutter_config["story_format"][0] == "sugarcube"


def test_include_github_workflow_is_yes_no_choice(cookiecutter_config: dict) -> None:
    assert cookiecutter_config["include_github_workflow"] == ["yes", "no"]
