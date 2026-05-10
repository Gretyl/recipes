"""Static checks against the Twee 3 source — runs without Chrome,
network, or a built dist.

The browser smoke in ``test_smoke.py`` is the integration gate but
requires headless Chrome and a compiled ``dist/index.html``; in a
sandboxed CI run those prerequisites are often absent, and the smoke
self-skips. These static tests give the bake at least one always-on
representative test so a punched-out project is green out of the box.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
IFID_RE = re.compile(r'"ifid"\s*:\s*"([^"]+)"')


def test_storydata_passage_present() -> None:
    """Twee 3 requires a StoryData special passage with the IFID and
    format declaration. Without it tweego refuses to build."""
    storydata = SRC / "StoryData.twee"
    assert storydata.is_file(), "src/StoryData.twee is required by Twee 3"
    content = storydata.read_text()
    assert content.lstrip().startswith(":: StoryData"), (
        "StoryData.twee must begin with the `:: StoryData` Twee 3 header"
    )


def test_storydata_carries_non_empty_ifid() -> None:
    """``post_gen_project.py`` mints a fresh UUID4 IFID at bake time
    when the cookiecutter prompt is left blank. A user-supplied IFID is
    preserved unchanged. Either way, the rendered StoryData must carry
    a non-empty IFID — Twee 3 rejects empty ones."""
    content = (SRC / "StoryData.twee").read_text()
    match = IFID_RE.search(content)
    assert match is not None, (
        "StoryData.twee must contain an `\"ifid\": \"...\"` line"
    )
    assert match.group(1).strip(), (
        "IFID must not be empty — post_gen_project should have replaced it"
    )


def test_start_passage_present() -> None:
    """The Start passage is the story's entry point; without it tweego
    errors at build time."""
    start = SRC / "Start.twee"
    assert start.is_file(), "src/Start.twee is required by Twee 3"
    content = start.read_text()
    assert content.lstrip().startswith(":: Start"), (
        "Start.twee must begin with the `:: Start` Twee 3 header"
    )
