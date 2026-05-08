"""Round 8 (network-gated): pin that `make dist` compiles src/*.twee
into dist/index.html and that the result is a real Twine HTML.

Twine's runtime distinguishes a story by reading the `<tw-storydata>`
element at the top of the body. Its `name` attribute is the story
title (drawn from src/StoryTitle.twee). If tweego didn't run, ran on
the wrong directory, or the StoryTitle never made it into the bake,
this element either won't be there or won't carry the user's title.

Skipped by default — opt in with TWEEGO_NETWORK_TESTS=1.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent

NETWORK_GATE = pytest.mark.skipif(
    os.environ.get("TWEEGO_NETWORK_TESTS") != "1",
    reason="network test; set TWEEGO_NETWORK_TESTS=1 to run",
)


@pytest.fixture(scope="module")
def built_dist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Bake → install tweego → make dist; returns the dist/index.html path."""
    out = tmp_path_factory.mktemp("dist-compile")
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(out))
    project = out / "my-narrative"

    install = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert install.returncode == 0, (
        f"install failed:\n{install.stdout}\n{install.stderr}"
    )

    dist = subprocess.run(
        ["make", "dist"],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert dist.returncode == 0, (
        f"make dist failed (rc={dist.returncode}):\n"
        f"stdout={dist.stdout}\nstderr={dist.stderr}"
    )

    html = project / "dist" / "index.html"
    return html


@NETWORK_GATE
@pytest.mark.network
def test_dist_html_exists_and_nonempty(built_dist: Path) -> None:
    assert built_dist.is_file(), f"dist/index.html missing at {built_dist}"
    # SugarCube + bundled stylesheet alone is already > 100KB; anything
    # smaller suggests tweego silently produced a stub.
    assert built_dist.stat().st_size > 100_000, (
        f"dist/index.html is suspiciously small ({built_dist.stat().st_size} bytes)"
    )


@NETWORK_GATE
@pytest.mark.network
def test_dist_html_contains_tw_storydata_element(built_dist: Path) -> None:
    content = built_dist.read_text()
    assert "<tw-storydata" in content, (
        "dist/index.html does not contain a <tw-storydata> element — "
        "tweego likely did not bind StoryData.twee correctly"
    )


@NETWORK_GATE
@pytest.mark.network
def test_dist_html_storydata_name_matches_title(built_dist: Path) -> None:
    """Default cookiecutter title 'An Untitled Room' must appear as the
    `name` attribute of <tw-storydata>, drawn through StoryTitle.twee."""
    content = built_dist.read_text()
    m = re.search(r'<tw-storydata\b[^>]*\bname="([^"]+)"', content)
    assert m, (
        "could not find name attribute on <tw-storydata>"
    )
    assert m.group(1) == "An Untitled Room", (
        f"<tw-storydata name=...> mismatch: got {m.group(1)!r}, "
        f"want 'An Untitled Room' (the cookiecutter title default)"
    )


@NETWORK_GATE
@pytest.mark.network
def test_dist_html_includes_start_passage_text(built_dist: Path) -> None:
    """The Start passage's body text reaches the bundled HTML — proves
    tweego didn't drop authored content somewhere along the way."""
    content = built_dist.read_text()
    # Start.twee has 'The room is dark.' as the first line of body.
    assert "The room is dark" in content, (
        "Start passage text not found in dist/index.html — tweego bundle "
        "is missing authored content"
    )
