"""Browser smoke test for {{ cookiecutter.project_slug }}.

Drives a real headless Chrome via the ``rodney`` CLI against
``dist/index.html`` (the tweego-compiled story). Each test asserts a
single user-visible property of the rendered story:

    1. The current passage renders with non-empty text content.
    2. Clicking the first internal link transitions to a different
       passage (proves the runtime is alive and link wiring is intact).

Selectors below are rendered at bake time for the chosen
``story_format`` ({{ cookiecutter.story_format }}). The four
tweego-bundled formats render passages differently:

    SugarCube:  #passages .passage    #passages a.link-internal
    Harlowe:    tw-passage            tw-link
    Chapbook:   .page                 .page a
    Snowman:    #story                #story a

Transition detection compares the passage container's textContent
before vs. after the click — that's format-agnostic, since SugarCube's
``data-passage`` attribute, Harlowe's ``<tw-passage>`` element, and
the others all change their text body when a new passage renders.

Run via ``make test`` after ``make setup-twine && make dist``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

{% if cookiecutter.story_format == "sugarcube" -%}
PASSAGE_SELECTOR = "#passages .passage"
LINK_SELECTOR = "#passages a.link-internal"
{% elif cookiecutter.story_format == "harlowe" -%}
PASSAGE_SELECTOR = "tw-passage"
LINK_SELECTOR = "tw-link"
{% elif cookiecutter.story_format == "chapbook" -%}
PASSAGE_SELECTOR = ".page"
LINK_SELECTOR = ".page a"
{% elif cookiecutter.story_format == "snowman" -%}
PASSAGE_SELECTOR = "#story"
LINK_SELECTOR = "#story a"
{%- endif %}
PASSAGE_TEXT_JS = (
    f"document.querySelector('{PASSAGE_SELECTOR}').textContent.trim()"
)


def _rodney(
    *args: str, check: bool = True, timeout: int = 30
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["uvx", "rodney", "--local", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"rodney {' '.join(args)} failed (rc={result.returncode}):\n"
            f"  stdout={result.stdout!r}\n"
            f"  stderr={result.stderr!r}"
        )
    return result


@pytest.fixture(scope="session")
def rodney_session(dist_html: Path):
    """Start rodney, open dist/index.html, wait for the story runtime
    to hydrate the start passage, yield to tests, then stop."""
    _rodney("start", timeout=60)
    try:
        _rodney("open", f"file://{dist_html}")
        # Network-idle alone isn't enough — the runtime still needs to
        # parse <tw-storydata> and render the start passage. Wait for
        # the passage container to appear.
        _rodney("wait", PASSAGE_SELECTOR, timeout=15)
        yield
    finally:
        _rodney("stop", check=False, timeout=10)


@pytest.mark.browser
def test_passage_renders_with_text(rodney_session: None) -> None:
    """The compiled story renders a passage with non-empty content."""
    text_len = _rodney(
        "js",
        f"document.querySelector('{PASSAGE_SELECTOR}').textContent.trim().length",
    ).stdout.strip()
    assert int(text_len) > 0, "passage rendered with empty text content"


@pytest.mark.browser
def test_first_link_transitions_passage(rodney_session: None) -> None:
    """Clicking the first internal link navigates to a different passage."""
    before = _rodney("js", PASSAGE_TEXT_JS).stdout.strip()
    assert before, "could not read starting passage's text content"

    _rodney("click", LINK_SELECTOR)
    # The runtime re-renders the passage container on transition; give
    # it a moment then re-query.
    _rodney("sleep", "0.5")

    after = _rodney("js", PASSAGE_TEXT_JS).stdout.strip()
    assert before != after, (
        f"link click did not transition passage (still on {before!r}) — "
        f"the runtime may not be hooked up, or the link selector "
        f"{LINK_SELECTOR!r} did not match the start passage's first link"
    )
