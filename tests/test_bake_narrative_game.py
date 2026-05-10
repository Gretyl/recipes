"""Bake-level tests for the narrative-game cookiecutter template.

Consolidates the nine working-dir test files from the upstream
``narrative-game/tests/`` into a single cookbook-rooted
suite that uses ``tests.helpers.bake``. Network-gated rounds (tweego
download, ``make dist`` compile, end-to-end ``make test`` smoke) are
``@pytest.mark.slow`` and additionally guarded by the
``TWEEGO_NETWORK_TESTS=1`` opt-in env var so the default ``make test``
run stays offline-clean.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
from typing import Any

import pytest
from cookiecutter.exceptions import FailedHookException
from cookiecutter.main import cookiecutter

from tests.helpers import COOKBOOK_DIR, bake, find_default_leaks, find_jinja_leaks

TEMPLATE_NAME = "narrative-game"
TEMPLATE_DIR = COOKBOOK_DIR / TEMPLATE_NAME
COOKIECUTTER_JSON = TEMPLATE_DIR / "cookiecutter.json"

# The four official Twine 2 story formats bundled with tweego.
# Paperthin is excluded — it's a story-format-authoring format, not a
# game-shipping format.
TWEEGO_BUNDLED_FORMATS = {"sugarcube", "harlowe", "chapbook", "snowman"}

# UUID4 canonical form: 8-4-4-4-12 hex; the third group starts with
# `4` (version), and the fourth group starts with one of {8,9,a,b}
# (variant).
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

NETWORK_GATE = pytest.mark.skipif(
    os.environ.get("TWEEGO_NETWORK_TESTS") != "1",
    reason="network test; set TWEEGO_NETWORK_TESTS=1 to run",
)


def _parse_storydata(project: pathlib.Path) -> dict[str, Any]:
    """Read src/StoryData.twee, strip the `:: StoryData` header, parse JSON."""
    text = (project / "src" / "StoryData.twee").read_text()
    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if line.strip()), None)
    assert header_idx is not None, "StoryData.twee has no header line"
    header = lines[header_idx].strip()
    assert header.startswith(":: StoryData"), (
        f"first non-empty line is not a StoryData header: {header!r}"
    )
    body = "\n".join(lines[header_idx + 1 :]).strip()
    data: dict[str, Any] = json.loads(body)
    return data


def _ifid_from_storydata(project: pathlib.Path) -> str:
    content = (project / "src" / "StoryData.twee").read_text()
    m = re.search(r'"ifid"\s*:\s*"([^"]*)"', content)
    assert m, f"no ifid key found in src/StoryData.twee:\n{content}"
    return m.group(1)


class TestCookiecutterJsonShape:
    """Pin the prompt set, defaults, and story-format choices in cookiecutter.json."""

    @pytest.fixture(scope="class")
    def config(self) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(COOKIECUTTER_JSON.read_text())
        return data

    def test_exposes_six_documented_prompts(self, config: dict[str, Any]) -> None:
        """The six prompts in the design doc are all present, no extras."""
        expected = {
            "project_slug",
            "title",
            "author_name",
            "story_format",
            "ifid",
            "include_github_workflow",
        }
        actual = {k for k in config if not k.startswith("_")}
        assert actual == expected, (
            f"prompts mismatch: missing={expected - actual}, "
            f"unexpected={actual - expected}"
        )

    def test_default_project_slug(self, config: dict[str, Any]) -> None:
        assert config["project_slug"] == "my-narrative"

    def test_default_title(self, config: dict[str, Any]) -> None:
        assert config["title"] == "An Untitled Room"

    def test_default_author_name(self, config: dict[str, Any]) -> None:
        assert config["author_name"] == "Anonymous"

    def test_default_ifid_is_empty_for_runtime_synthesis(
        self, config: dict[str, Any]
    ) -> None:
        """An empty IFID signals post_gen_project to mint a fresh UUID4."""
        assert config["ifid"] == ""

    def test_story_format_choices_match_tweego_bundled(
        self, config: dict[str, Any]
    ) -> None:
        formats = config["story_format"]
        assert isinstance(formats, list)
        assert len(formats) == 4, f"expected 4 story formats, got {len(formats)}"
        assert set(formats) == TWEEGO_BUNDLED_FORMATS

    def test_story_format_default_is_sugarcube(self, config: dict[str, Any]) -> None:
        """First element of a cookiecutter choice list is the default."""
        formats = config["story_format"]
        assert isinstance(formats, list)
        assert formats[0] == "sugarcube"

    def test_include_github_workflow_is_yes_no_choice(
        self, config: dict[str, Any]
    ) -> None:
        assert config["include_github_workflow"] == ["yes", "no"]


class TestPreGenSlugValidation:
    """pre_gen_project rejects malformed slugs before any files render."""

    BAD_SLUGS = [
        pytest.param("MyNarrative", id="uppercase"),
        pytest.param("-my-narrative", id="leading-hyphen"),
        pytest.param("my narrative", id="contains-space"),
        pytest.param("my_narrative!", id="contains-punctuation"),
    ]

    GOOD_SLUGS = [
        pytest.param("my-narrative", id="default"),
        pytest.param("abc", id="short"),
        pytest.param("a-b-c", id="hyphenated"),
        pytest.param("x123", id="alphanumeric"),
    ]

    @pytest.mark.parametrize("bad_slug", BAD_SLUGS)
    def test_pre_gen_rejects_bad_slug(
        self,
        bad_slug: str,
        tmp_path: pathlib.Path,
        capfd: pytest.CaptureFixture[str],
    ) -> None:
        """Bad slug raises FailedHookException; hook stderr names the slug;
        no project dir is left behind on disk."""
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
        leftover = list(tmp_path.iterdir())
        assert leftover == [], (
            f"output directory should be empty after hook rejection, "
            f"but found: {[p.name for p in leftover]}"
        )

    @pytest.mark.parametrize("good_slug", GOOD_SLUGS)
    def test_pre_gen_accepts_good_slug(
        self, good_slug: str, tmp_path: pathlib.Path
    ) -> None:
        cookiecutter(
            str(TEMPLATE_DIR),
            no_input=True,
            output_dir=str(tmp_path),
            extra_context={"project_slug": good_slug},
        )
        assert (tmp_path / good_slug).is_dir()


class TestBakeDefaults:
    """Bake with default context — source passages, build harness, IFID synthesis."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake(TEMPLATE_NAME, tmp_path_factory.mktemp("defaults"))

    def test_output_directory_exists(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()
        assert baked.name == "my-narrative"

    @pytest.mark.parametrize(
        "relpath",
        [
            "src/StoryData.twee",
            "src/StoryTitle.twee",
            "src/StoryStylesheet.twee",
            "src/StoryScript.twee",
            "src/StoryInit.twee",
            "src/Start.twee",
        ],
    )
    def test_required_source_passage_exists(
        self, baked: pathlib.Path, relpath: str
    ) -> None:
        target = baked / relpath
        assert target.is_file(), f"missing required source passage: {relpath}"
        assert target.read_text().strip(), f"source passage {relpath} is empty"

    def test_storydata_declares_passage_header(self, baked: pathlib.Path) -> None:
        """Twee 3 special passages start with `:: StoryData`."""
        content = (baked / "src" / "StoryData.twee").read_text()
        assert content.lstrip().startswith(":: StoryData")

    def test_start_passage_header(self, baked: pathlib.Path) -> None:
        content = (baked / "src" / "Start.twee").read_text()
        assert content.lstrip().startswith(":: Start")

    @pytest.mark.parametrize(
        "relpath",
        [
            "Makefile",
            "pyproject.toml",
            "README.md",
            ".gitignore",
            "scripts/install-tweego.sh",
            "tests/conftest.py",
            "tests/test_smoke.py",
        ],
    )
    def test_required_harness_file(self, baked: pathlib.Path, relpath: str) -> None:
        target = baked / relpath
        assert target.is_file(), f"missing harness file: {relpath}"
        assert target.read_text().strip(), f"harness file {relpath} is empty"

    def test_install_tweego_script_is_executable(self, baked: pathlib.Path) -> None:
        script = baked / "scripts" / "install-tweego.sh"
        mode = script.stat().st_mode
        assert mode & stat.S_IXUSR, (
            f"install-tweego.sh is not executable (mode={oct(mode)})"
        )

    def test_makefile_declares_required_targets(self, baked: pathlib.Path) -> None:
        """`make test` is the cookbook's single pre-commit gate; the rest are
        the layered targets it composes."""
        content = (baked / "Makefile").read_text()
        for target in ("setup-twine:", "test:", "clean:"):
            assert target in content, f"Makefile missing target: {target}"
        # `dist` may appear as `dist:` or `dist/index.html:`; accept either.
        nonblank = [
            line
            for line in content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        assert any(line.startswith("dist") and ":" in line for line in nonblank), (
            "Makefile must declare a `dist` target"
        )

    def test_makefile_uses_tweego_detection_idiom(self, baked: pathlib.Path) -> None:
        """`command -v tweego` + `ifdef`/`ifeq` skip-with-warning per the
        non-Python toolchain pattern. Keeps the build green on hosts
        without tweego installed."""
        content = (baked / "Makefile").read_text()
        assert "TWEEGO" in content
        assert "command -v tweego" in content
        assert "ifdef TWEEGO" in content or "ifeq" in content

    def test_gitignore_excludes_build_artifacts(self, baked: pathlib.Path) -> None:
        content = (baked / ".gitignore").read_text()
        for pattern in ("dist/", ".tweego/"):
            assert pattern in content

    def test_baked_pyproject_declares_rodney_dev_dep(self, baked: pathlib.Path) -> None:
        content = (baked / "pyproject.toml").read_text()
        assert "rodney" in content.lower()
        assert "pytest" in content

    def test_baked_pyproject_targets_python_3_13(self, baked: pathlib.Path) -> None:
        """Cookbook AGENTS.md sets 3.13 as the cookbook-wide Python target."""
        content = (baked / "pyproject.toml").read_text()
        assert ">=3.13" in content, (
            f"baked pyproject.toml does not target Python 3.13: {content!r}"
        )

    def test_install_tweego_detects_platform(self, baked: pathlib.Path) -> None:
        """uname-based OS/arch branch — without it, the binary downloaded
        on darwin-arm64 could be a linux-x64 ELF and fail silently."""
        content = (baked / "scripts" / "install-tweego.sh").read_text()
        assert "uname" in content

    def test_readme_mentions_tweego(self, baked: pathlib.Path) -> None:
        content = (baked / "README.md").read_text().lower()
        assert "tweego" in content

    def test_default_ifid_is_a_canonical_uuid4(self, baked: pathlib.Path) -> None:
        """Empty IFID default → post_gen synthesises a UUID4 in StoryData."""
        ifid = _ifid_from_storydata(baked)
        assert ifid != "", "blank IFID survived into StoryData — synthesis didn't run"
        assert UUID4_RE.match(ifid), f"synthesised IFID is not UUID4: {ifid!r}"

    def test_storydata_start_passage_is_named_start(self, baked: pathlib.Path) -> None:
        """The `start` key names the entry passage; we ship Start.twee."""
        data = _parse_storydata(baked)
        assert data["start"] == "Start"

    def test_storytitle_renders_title_under_header(self, baked: pathlib.Path) -> None:
        """StoryTitle's body feeds tweego's `<tw-storydata name="...">`
        attribute. The default cookiecutter title must land under the
        `:: StoryTitle` header — without that, the compiled HTML
        identifies the story as an empty string."""
        content = (baked / "src" / "StoryTitle.twee").read_text()
        assert content.lstrip().startswith(":: StoryTitle"), (
            "StoryTitle.twee must begin with `:: StoryTitle` Twee 3 header"
        )
        assert "An Untitled Room" in content, (
            f"default cookiecutter title not in StoryTitle.twee:\n{content!r}"
        )

    def test_storystylesheet_carries_stylesheet_tag(self, baked: pathlib.Path) -> None:
        """The `[stylesheet]` tag on the StoryStylesheet header is what
        tells tweego the body is CSS, not Twee. Without it, the body
        renders as a passage instead of injecting a `<style>` element."""
        content = (baked / "src" / "StoryStylesheet.twee").read_text()
        assert content.lstrip().startswith(":: StoryStylesheet [stylesheet]"), (
            f"StoryStylesheet.twee header missing `[stylesheet]` tag:\n"
            f"{content[:200]!r}"
        )

    def test_storystylesheet_ships_diegetic_ui_defaults(
        self, baked: pathlib.Path
    ) -> None:
        """The default stylesheet is the template's *starting marks* —
        dim background, monospaced narrow column, restyled buttons and
        internal links. These are documented in the demo as freely
        editable but must be the bake's starting point so the first
        `make dist` looks the part."""
        content = (baked / "src" / "StoryStylesheet.twee").read_text()
        assert "body {" in content, "stylesheet must define a body rule"
        assert "background:" in content, (
            "stylesheet must set a background colour (the diegetic dim ground)"
        )
        assert "monospace" in content, "stylesheet must declare a monospace font stack"
        assert ".link-internal" in content or "a.link-internal" in content, (
            "stylesheet must restyle SugarCube's `.link-internal` class — "
            "without that, the default `[[Wait]]` link renders as a "
            "browser-default underlined hyperlink"
        )

    def test_storyscript_carries_script_tag(self, baked: pathlib.Path) -> None:
        """The `[script]` tag on the StoryScript header is what tells
        tweego the body is JS. Without it, the body renders as a
        passage instead of injecting a `<script>` element."""
        content = (baked / "src" / "StoryScript.twee").read_text()
        assert content.lstrip().startswith(":: StoryScript [script]"), (
            f"StoryScript.twee header missing `[script]` tag:\n{content[:200]!r}"
        )

    def test_storyinit_seeds_initial_state(self, baked: pathlib.Path) -> None:
        """StoryInit runs once at story start and is where authors
        initialise variables. The default bake seeds at least one
        SugarCube `<<set ...>>` macro so authors have a working pattern
        to copy from rather than an empty file."""
        content = (baked / "src" / "StoryInit.twee").read_text()
        assert content.lstrip().startswith(":: StoryInit"), (
            "StoryInit.twee must begin with `:: StoryInit` Twee 3 header"
        )
        assert "<<set" in content, (
            "StoryInit.twee must seed at least one SugarCube `<<set ...>>` "
            "macro so authors have a starting pattern"
        )

    def test_agents_md_exists(self, baked: pathlib.Path) -> None:
        """`narrative-game` is a standalone Twine workbench. By the cookbook
        pattern (matching `python-project` and `artifact-bench`), it ships
        an `AGENTS.md` at the project root scoped to agent-only conventions
        that have no other home."""
        assert (baked / "AGENTS.md").is_file()

    def test_claude_md_delegates_to_agents(self, baked: pathlib.Path) -> None:
        """`CLAUDE.md` is a one-line delegation stub so both filenames
        resolve to the same guidance. Same pattern as python-project and
        artifact-bench."""
        claude = baked / "CLAUDE.md"
        assert claude.is_file()
        assert claude.read_text() == "@AGENTS.md\n"


class TestIfidSynthesis:
    """post_gen_project IFID handling: blank → UUID4, user-supplied → preserved."""

    def test_two_blank_bakes_produce_different_ifids(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        out1 = bake(TEMPLATE_NAME, tmp_path_factory.mktemp("ifid-a"))
        out2 = bake(TEMPLATE_NAME, tmp_path_factory.mktemp("ifid-b"))
        ifid1 = _ifid_from_storydata(out1)
        ifid2 = _ifid_from_storydata(out2)
        assert ifid1 != ifid2, (
            f"two bakes produced the same IFID ({ifid1!r}) — likely hard-coded"
        )

    def test_user_supplied_ifid_is_preserved(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """An explicit IFID flows through unchanged. Uppercase form is
        deliberate — synthesis must not normalise case."""
        explicit = "DEADBEEF-CAFE-4BAD-8FED-FEEDFACEC0DE"
        baked = bake(
            TEMPLATE_NAME,
            tmp_path_factory.mktemp("ifid-user"),
            extra_context={"ifid": explicit},
        )
        assert _ifid_from_storydata(baked) == explicit


class TestBakePerStoryFormat:
    """Each story_format choice yields a parseable StoryData with the
    canonical Twine name (not the lowercase prompt value)."""

    @pytest.fixture(
        scope="class",
        params=[
            pytest.param(("sugarcube", "SugarCube"), id="sugarcube"),
            pytest.param(("harlowe", "Harlowe"), id="harlowe"),
            pytest.param(("chapbook", "Chapbook"), id="chapbook"),
            pytest.param(("snowman", "Snowman"), id="snowman"),
        ],
    )
    def baked_per_format(
        self,
        request: pytest.FixtureRequest,
        tmp_path_factory: pytest.TempPathFactory,
    ) -> tuple[pathlib.Path, str, str]:
        choice, canonical = request.param
        baked = bake(
            TEMPLATE_NAME,
            tmp_path_factory.mktemp(f"format-{choice}"),
            extra_context={"story_format": choice},
        )
        return baked, choice, canonical

    def test_format_mapping_to_canonical_name(
        self, baked_per_format: tuple[pathlib.Path, str, str]
    ) -> None:
        baked, choice, canonical = baked_per_format
        data = _parse_storydata(baked)
        assert data["format"] == canonical, (
            f"{choice!r} should render as {canonical!r}, got {data['format']!r}"
        )

    def test_storydata_json_well_formed(
        self, baked_per_format: tuple[pathlib.Path, str, str]
    ) -> None:
        baked, _choice, _canonical = baked_per_format
        data = _parse_storydata(baked)
        assert isinstance(data, dict)
        assert "ifid" in data
        assert "format" in data
        assert "start" in data

    def test_storydata_ifid_is_uuid4(
        self, baked_per_format: tuple[pathlib.Path, str, str]
    ) -> None:
        baked, _choice, _canonical = baked_per_format
        data = _parse_storydata(baked)
        ifid = data["ifid"]
        assert isinstance(ifid, str) and UUID4_RE.match(ifid), (
            f"ifid {ifid!r} is not a canonical UUID4"
        )


class TestBakedSmokeSelectorsAreFormatAware:
    """The baked `tests/test_smoke.py` carries the right DOM selectors
    for the chosen story_format.

    SugarCube renders passages as `#passages .passage[data-passage]` with
    internal links classed `a.link-internal`; Harlowe uses `<tw-passage>`
    with `<tw-link>` elements; Chapbook uses a `.page` container with
    plain `<a>` links; Snowman uses `#story` with plain `<a>` links. A
    smoke file that hardcodes one format's selectors greens or reds
    against the wrong DOM when a downstream user picks any other
    format — every assertion either misses the element entirely
    (silent skip) or matches a wholly different element (false-positive
    pass / false-negative fail).
    """

    EXPECTED_SELECTORS = [
        pytest.param(
            ("sugarcube", "#passages .passage", "#passages a.link-internal"),
            id="sugarcube",
        ),
        pytest.param(("harlowe", "tw-passage", "tw-link"), id="harlowe"),
        pytest.param(("chapbook", ".page", ".page a"), id="chapbook"),
        pytest.param(("snowman", "#story", "#story a"), id="snowman"),
    ]

    @pytest.fixture(scope="class", params=EXPECTED_SELECTORS)
    def baked_smoke(
        self,
        request: pytest.FixtureRequest,
        tmp_path_factory: pytest.TempPathFactory,
    ) -> tuple[str, str, str, str]:
        story_format, passage_selector, link_selector = request.param
        baked = bake(
            TEMPLATE_NAME,
            tmp_path_factory.mktemp(f"smoke-sel-{story_format}"),
            extra_context={"story_format": story_format},
        )
        smoke = (baked / "tests" / "test_smoke.py").read_text()
        return story_format, passage_selector, link_selector, smoke

    def test_baked_smoke_carries_format_specific_passage_selector(
        self, baked_smoke: tuple[str, str, str, str]
    ) -> None:
        story_format, passage_selector, link_selector, smoke = baked_smoke
        assert f'PASSAGE_SELECTOR = "{passage_selector}"' in smoke, (
            f"expected PASSAGE_SELECTOR = {passage_selector!r} for "
            f"story_format={story_format!r}, but the baked smoke does not "
            f"carry that selector. The smoke template likely still ships "
            f"SugarCube's selectors regardless of the chosen format."
        )
        assert f'LINK_SELECTOR = "{link_selector}"' in smoke, (
            f"expected LINK_SELECTOR = {link_selector!r} for "
            f"story_format={story_format!r}, but the baked smoke does not "
            f"carry that selector."
        )

    def test_baked_smoke_does_not_leak_other_formats_selectors(
        self, baked_smoke: tuple[str, str, str, str]
    ) -> None:
        """Inverse-branch sweep: a Harlowe bake must not carry SugarCube's
        `.link-internal` constant, a Chapbook bake must not carry
        `<tw-passage>`, etc. Without this guard, a Jinja conditional that
        falls through silently could ship selectors from the wrong format
        even while the assertion above passes."""
        story_format, _passage_selector, _link_selector, smoke = baked_smoke
        other_format_markers = {
            "sugarcube": ["link-internal", "#passages"],
            "harlowe": ["tw-passage", "tw-link"],
            "chapbook": ['".page"'],
            "snowman": ['"#story"'],
        }
        # Strip the docstring's selector-swap reference table; the leak
        # check is about live code, not commentary.
        body = smoke.split('"""', 2)[-1] if smoke.count('"""') >= 2 else smoke
        for other, markers in other_format_markers.items():
            if other == story_format:
                continue
            for marker in markers:
                assert marker not in body, (
                    f"baked smoke for story_format={story_format!r} leaks "
                    f"{other!r}'s selector marker {marker!r} into live code "
                    f"— the per-format Jinja branch is bleeding through"
                )


class TestBakeCustomContext:
    """Bake with custom values for every variable — defaults must not leak."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake(
            TEMPLATE_NAME,
            tmp_path_factory.mktemp("custom"),
            extra_context={
                "project_slug": "the-cold-room",
                "title": "The Cold Room",
                "author_name": "Avery Cole",
                "story_format": "harlowe",
                "ifid": "12345678-1234-4234-8234-123456789012",
                "include_github_workflow": "no",
            },
        )

    def test_custom_project_slug_names_output_directory(
        self, baked: pathlib.Path
    ) -> None:
        assert baked.is_dir()
        assert baked.name == "the-cold-room"

    def test_custom_project_slug_propagates_to_pyproject(
        self, baked: pathlib.Path
    ) -> None:
        content = (baked / "pyproject.toml").read_text()
        assert 'name = "the-cold-room"' in content

    def test_custom_title_propagates_to_storytitle(self, baked: pathlib.Path) -> None:
        """StoryTitle.twee feeds tweego's <tw-storydata name="..."> attribute."""
        content = (baked / "src" / "StoryTitle.twee").read_text()
        assert "The Cold Room" in content

    def test_custom_author_propagates_to_pyproject(self, baked: pathlib.Path) -> None:
        content = (baked / "pyproject.toml").read_text()
        assert "Avery Cole" in content

    def test_custom_story_format_lands_canonical(self, baked: pathlib.Path) -> None:
        data = _parse_storydata(baked)
        assert data["format"] == "Harlowe"

    def test_custom_ifid_preserved(self, baked: pathlib.Path) -> None:
        assert _ifid_from_storydata(baked) == "12345678-1234-4234-8234-123456789012"

    def test_no_default_values_leak_into_text_files(self, baked: pathlib.Path) -> None:
        """Sweep every text file (including .twee) for the cookiecutter
        defaults — any hit means a hardcoded substring escaped Jinja
        substitution. `.twee` is in the suffix list because cookiecutter
        renders all files by default; the recipes generalize tool only
        scans .py/.toml/.md/.json/.yaml/.yml/.txt for round-tripping,
        but the bake output itself must still be Jinja-clean."""
        leaks = find_default_leaks(
            baked,
            defaults=("my-narrative", "An Untitled Room", "Anonymous"),
            suffixes={
                ".md",
                ".toml",
                ".json",
                ".yaml",
                ".yml",
                ".txt",
                ".twee",
                ".sh",
                ".py",
            },
            extra_names={"Makefile", ".gitignore"},
        )
        assert not leaks, f"default values leaked into custom-context bake: {leaks}"

    def test_no_unrendered_cookiecutter_tokens(self, baked: pathlib.Path) -> None:
        """An unrendered `{{ cookiecutter.* }}` is a Jinja substitution that
        the engine missed. Twee/SugarCube/Harlowe use `<<…>>` and `[[…]]`;
        JSON uses single `{`/`}`. Double braces are unambiguously a
        leftover Jinja token."""
        offenders = find_jinja_leaks(baked)
        assert not offenders, f"unrendered Jinja2 markers in: {offenders}"


# ---------------------------------------------------------------------------
# Network + browser-gated end-to-end tests. Run only when explicitly opted
# in via TWEEGO_NETWORK_TESTS=1; mirror the artifact-bench
# `test_baked_artifact_bench_verify_job_runs_green` slow-marked pattern.
# These prove the install script downloads a working tweego, that
# `make dist` compiles a real Twine HTML, and that the baked rodney
# smoke greens up under the cookbook-canonical `make test` gate.
# ---------------------------------------------------------------------------


@NETWORK_GATE
@pytest.mark.slow()
@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_baked_install_tweego_downloads_runnable_binary(
    tmp_path: pathlib.Path,
) -> None:
    """A cold bake → ./scripts/install-tweego.sh produces an executable
    .tweego/tweego that prints a version string. Re-running is idempotent
    (announces "already installed") and ships story formats for all four
    bundled choices."""
    baked = bake(TEMPLATE_NAME, tmp_path)

    install = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=baked,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert install.returncode == 0, (
        f"install-tweego.sh failed:\n{install.stdout}\n{install.stderr}"
    )

    bin_path = baked / ".tweego" / "tweego"
    assert bin_path.is_file(), f"binary missing at {bin_path}"
    assert bin_path.stat().st_mode & stat.S_IXUSR, "binary not executable"

    version = subprocess.run(
        [str(bin_path), "-v"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    output = (version.stdout + version.stderr).lower()
    assert "tweego" in output and "version" in output, (
        f"tweego -v output unexpected: {output!r}"
    )

    for subdir in ("sugarcube-2", "harlowe-3", "chapbook-1", "snowman-2"):
        fmt_dir = baked / ".tweego" / "storyformats" / subdir
        assert fmt_dir.is_dir(), f"missing story format {subdir}"

    rerun = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=baked,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert rerun.returncode == 0
    rerun_output = (rerun.stdout + rerun.stderr).lower()
    assert "already installed" in rerun_output, (
        f"second install did not skip via idempotency check: {rerun_output!r}"
    )


@NETWORK_GATE
@pytest.mark.slow()
@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_baked_make_dist_produces_valid_twine_html(
    tmp_path: pathlib.Path,
) -> None:
    """A cold bake → setup-twine → `make dist` produces dist/index.html
    >100 KB carrying a `<tw-storydata name="An Untitled Room">` element
    and the Start passage's authored body text."""
    baked = bake(TEMPLATE_NAME, tmp_path)

    install = subprocess.run(
        ["./scripts/install-tweego.sh"],
        cwd=baked,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert install.returncode == 0, (
        f"install failed:\n{install.stdout}\n{install.stderr}"
    )

    dist = subprocess.run(
        ["make", "dist"],
        cwd=baked,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert dist.returncode == 0, f"make dist failed:\n{dist.stdout}\n{dist.stderr}"

    html_path = baked / "dist" / "index.html"
    assert html_path.is_file()
    assert html_path.stat().st_size > 100_000, (
        f"dist/index.html suspiciously small ({html_path.stat().st_size} bytes)"
    )
    content = html_path.read_text()
    assert "<tw-storydata" in content
    m = re.search(r'<tw-storydata\b[^>]*\bname="([^"]+)"', content)
    assert m, "no name= attribute on <tw-storydata>"
    assert m.group(1) == "An Untitled Room"
    assert "The room is dark" in content, (
        "Start passage body text missing from compiled HTML"
    )


@NETWORK_GATE
@pytest.mark.slow()
@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_baked_make_test_runs_rodney_smoke_green(
    tmp_path: pathlib.Path,
) -> None:
    """End-to-end gate: cold bake → `make test` (chains setup-twine → dist
    → pytest under rodney). Mirrors what a contributor running the
    cookbook's pre-commit gate would do. The baked pytest config sets
    `addopts = "-q"` so individual test names are suppressed; assert on
    the durable `N passed` summary line instead."""
    baked = bake(TEMPLATE_NAME, tmp_path)

    result = subprocess.run(
        ["make", "test"],
        cwd=baked,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"make test failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "2 passed" in result.stdout, (
        f"expected '2 passed' in make test output:\n{result.stdout}"
    )
