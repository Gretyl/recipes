"""Round 4: pin pre_gen_project.py's slug-validation behaviour.

A `project_slug` containing uppercase, leading hyphen, spaces,
punctuation, or empty string must be rejected with a clear message
*before* any project files are written. Cookiecutter's
``FailedHookException`` is the surface signal.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from cookiecutter.exceptions import FailedHookException
from cookiecutter.main import cookiecutter

TEMPLATE_DIR = Path(__file__).parent.parent


BAD_SLUGS = [
    pytest.param("MyNarrative", id="uppercase"),
    pytest.param("-my-narrative", id="leading-hyphen"),
    pytest.param("my narrative", id="contains-space"),
    pytest.param("my_narrative!", id="contains-punctuation"),
    # Empty-string is intercepted by cookiecutter itself before any
    # hook runs (the output dir collides with tmp_path), so it isn't
    # the hook's responsibility to reject.
]

GOOD_SLUGS = [
    pytest.param("my-narrative", id="default"),
    pytest.param("abc", id="short"),
    pytest.param("a-b-c", id="hyphenated"),
    pytest.param("x123", id="alphanumeric"),
]


@pytest.mark.parametrize("bad_slug", BAD_SLUGS)
def test_pre_gen_rejects_bad_slug(
    bad_slug: str, tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """A bad slug raises FailedHookException; the hook's stderr (captured
    via capfd at the fd level, since the hook runs in a subprocess) names
    the slug; no project dir is left behind on disk."""
    with pytest.raises(FailedHookException):
        cookiecutter(
            str(TEMPLATE_DIR),
            no_input=True,
            output_dir=str(tmp_path),
            extra_context={"project_slug": bad_slug},
        )
    captured = capfd.readouterr()
    combined = (captured.out + captured.err).lower()
    assert "slug" in combined or "project_slug" in combined, (
        f"hook output did not mention the slug. "
        f"stdout={captured.out!r}, stderr={captured.err!r}"
    )
    # Cookiecutter cleans up partially-rendered output on hook failure.
    leftover = [p for p in tmp_path.iterdir()]
    assert leftover == [], (
        f"output directory should be empty after hook rejection, "
        f"but found: {[p.name for p in leftover]}"
    )


@pytest.mark.parametrize("good_slug", GOOD_SLUGS)
def test_pre_gen_accepts_good_slug(good_slug: str, tmp_path: Path) -> None:
    """A valid slug bakes cleanly into a directory of that name."""
    cookiecutter(
        str(TEMPLATE_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"project_slug": good_slug},
    )
    assert (tmp_path / good_slug).is_dir(), (
        f"expected baked project at {tmp_path / good_slug}"
    )
