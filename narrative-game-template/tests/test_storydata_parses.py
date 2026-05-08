"""Round 6 (test-after): pin StoryData parses as Twee 3 + JSON, with
canonical story-format names across all four bundled choices.

The behaviour pinned here was established jointly by rounds 1 (the
prompt list and `_format_proper` mapping in cookiecutter.json), 2
(the StoryData.twee template body), and 5 (UUID4 synthesis). This
test guards the seam that ties them together — if any future change
breaks JSON validity in StoryData, drops the canonical capitalisation
on a story format, or lets the lowercase prompt value leak through,
this suite catches it.

This is a test-after round per AGENTS.md: one commit, not two.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent

UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Each cookiecutter choice → its canonical Twine story-format name as
# tweego expects it in StoryData metadata.
FORMAT_MAPPING = [
    pytest.param("sugarcube", "SugarCube", id="sugarcube"),
    pytest.param("harlowe", "Harlowe", id="harlowe"),
    pytest.param("chapbook", "Chapbook", id="chapbook"),
    pytest.param("snowman", "Snowman", id="snowman"),
]


def _parse_storydata(project: Path) -> dict:
    """Read src/StoryData.twee, strip the `:: StoryData` header line,
    and parse the JSON body. Returns the parsed dict."""
    text = (project / "src" / "StoryData.twee").read_text()
    lines = text.splitlines()
    assert lines, "StoryData.twee is empty"
    # The header is the first non-empty line and must start with `::`.
    header_idx = next(
        (i for i, line in enumerate(lines) if line.strip()),
        None,
    )
    assert header_idx is not None, "StoryData.twee has no header line"
    header = lines[header_idx].strip()
    assert header.startswith(":: StoryData"), (
        f"first non-empty line is not a StoryData header: {header!r}"
    )
    body = "\n".join(lines[header_idx + 1 :]).strip()
    return json.loads(body)


@pytest.mark.parametrize("choice,canonical", FORMAT_MAPPING)
def test_format_mapping_covers_all_four_story_formats(
    choice: str, canonical: str, tmp_path: Path
) -> None:
    """Each cookiecutter story_format choice yields the canonical name
    that tweego/Twine expects."""
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"story_format": choice},
    )
    data = _parse_storydata(tmp_path / "my-narrative")
    assert data["format"] == canonical, (
        f"{choice!r} should render as {canonical!r}, got {data['format']!r} — "
        f"the lowercase prompt value must not leak through"
    )


@pytest.mark.parametrize("choice,_canonical", FORMAT_MAPPING)
def test_storydata_json_is_well_formed_across_formats(
    choice: str, _canonical: str, tmp_path: Path
) -> None:
    """The JSON body parses cleanly regardless of which format was chosen."""
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"story_format": choice},
    )
    # _parse_storydata raises json.JSONDecodeError on malformed JSON
    data = _parse_storydata(tmp_path / "my-narrative")
    assert isinstance(data, dict), "StoryData JSON body must be a JSON object"
    assert "ifid" in data, "StoryData must declare an `ifid`"
    assert "format" in data, "StoryData must declare a `format`"
    assert "start" in data, "StoryData must declare a `start` passage"


@pytest.mark.parametrize("choice,_canonical", FORMAT_MAPPING)
def test_storydata_ifid_is_uuid4_across_formats(
    choice: str, _canonical: str, tmp_path: Path
) -> None:
    """The synthesised IFID is a canonical UUID4 regardless of story format."""
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"story_format": choice},
    )
    data = _parse_storydata(tmp_path / "my-narrative")
    assert UUID4_RE.match(data["ifid"]), (
        f"ifid {data['ifid']!r} is not a canonical UUID4"
    )


def test_storydata_start_passage_is_named_start(tmp_path: Path) -> None:
    """The `start` key names the entry passage. We ship Start.twee, so
    this must be 'Start' for the bake to produce a runnable story."""
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(tmp_path))
    data = _parse_storydata(tmp_path / "my-narrative")
    assert data["start"] == "Start", (
        f"start passage must be 'Start' (matches src/Start.twee), "
        f"got {data['start']!r}"
    )
