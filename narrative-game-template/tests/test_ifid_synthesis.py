"""Round 5: pin IFID-synthesis behaviour.

Twee 3 requires every story to declare an Interactive Fiction
IDentifier (IFID) — a UUID4 — in its StoryData passage. The
``ifid`` cookiecutter prompt defaults to ``""``; the hook layer must
mint a fresh UUID4 in that case, and pass through a user-supplied
IFID unchanged.

Implementation surface: post_gen_project.py edits the rendered
src/StoryData.twee in place. (pre_gen runs before rendering and
cannot mutate the context cookiecutter uses to render files.) The
test asserts the outcome — the IFID landing in StoryData.twee — and
is agnostic to which hook synthesises it.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent

# UUID4 canonical form: 8-4-4-4-12 hex; the third group starts with
# `4` (version), and the fourth group starts with one of {8,9,a,b}
# (variant). Match case-insensitively because Twee 3 accepts either.
UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _ifid_from_storydata(project: Path) -> str:
    content = (project / "src" / "StoryData.twee").read_text()
    m = re.search(r'"ifid"\s*:\s*"([^"]*)"', content)
    assert m, (
        f"no ifid key found in src/StoryData.twee:\n{content}"
    )
    return m.group(1)


def test_blank_ifid_synthesises_uuid4(tmp_path: Path) -> None:
    """Default bake (ifid='' in cookiecutter.json) mints a fresh UUID4."""
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(tmp_path))
    ifid = _ifid_from_storydata(tmp_path / "my-narrative")
    assert ifid != "", "blank IFID survived into StoryData — synthesis didn't run"
    assert UUID4_RE.match(ifid), (
        f"synthesised IFID is not a canonical UUID4: {ifid!r}"
    )


def test_two_blank_bakes_produce_different_ifids(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    """Two consecutive default bakes mint *different* UUIDs (not a constant)."""
    out1 = tmp_path_factory.mktemp("ifid-a")
    out2 = tmp_path_factory.mktemp("ifid-b")
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(out1))
    cookiecutter(str(TEMPLATE_DIR), no_input=True, output_dir=str(out2))
    ifid1 = _ifid_from_storydata(out1 / "my-narrative")
    ifid2 = _ifid_from_storydata(out2 / "my-narrative")
    assert ifid1 != ifid2, (
        f"two bakes produced the same IFID ({ifid1!r}) — likely a hard-coded constant"
    )


def test_user_supplied_ifid_is_preserved(tmp_path: Path) -> None:
    """An explicit IFID flows through to StoryData unchanged.

    Uppercase form deliberately — synthesis must not normalise case.
    """
    explicit = "DEADBEEF-CAFE-4BAD-8FED-FEEDFACEC0DE"
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"ifid": explicit},
    )
    ifid = _ifid_from_storydata(tmp_path / "my-narrative")
    assert ifid == explicit, (
        f"user-supplied IFID was rewritten: got {ifid!r}, want {explicit!r}"
    )
