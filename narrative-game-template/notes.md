# notes.md — `narrative-game-template`

TDD round log. Each round = 1 RED commit + 1 GREEN commit (rounds 6,
8, 9 are `test-after`, single commit).

## Cookbook integration reshape (post-round-9)

After completing rounds 1–9, the working was reshaped against the
actual Gretyl/recipes `cookbook/` conventions (read directly from the
public repo since the MCP scope is gretyl/grimoire-only):

  - **Flat entry root.** Dropped the `template/` wrapper. The
    cookiecutter root (`cookiecutter.json`, `hooks/`,
    `{{cookiecutter.project_slug}}/`) lives directly under the
    working dir, matching `cookbook/repo-cli/` and
    `cookbook/python-project/`. Cookiecutter ignores non-template
    files at the same level (AGENTS.md, README.md, charts/, tests/,
    etc.), so the working metadata coexists fine.
  - **`make test` as the single pre-commit gate.** Renamed the baked
    Makefile's `verify` target to `test`, per cookbook AGENTS.md.
    Implementation switched from prerequisite chain to sub-make calls
    (`$(MAKE) setup-twine; $(MAKE) dist; pytest`) — the original
    chain had a parse-time / runtime ordering bug where TWEEGO was
    detected before setup-twine had populated `.tweego/`, so the
    very first `make test` produced a stub dist and pytest skipped.
  - **showboat-built demo.md.** Rebuilt via
    `showboat init/note/exec/image`; passes `showboat verify` with
    exit 0. Display-only Twee snippets use HTML `<pre><code>` so
    showboat's verify (which tries to exec all fenced blocks) leaves
    them alone.
  - **Test-after lands.** The e2e smoke now drives `make test`
    instead of running `uv run pytest` directly, mirroring what a
    cookbook reviewer would do.

Out-of-scope for this working (left to the cross-repo PR):

  - Migrating tests/ to cookbook root's `tests/test_bake_*.py`
    layout (cookbook tests live at the recipes-repo root, not in the
    entry).
  - Splitting `notes.md` and `demo.md` into the cookbook's
    `notes/` and `demos/` shared dirs.
  - Bumping baked Python from 3.11 to 3.13 — the cookbook expects
    3.13, but per the artifact-bench precedent in cookbook AGENTS.md,
    non-Python entries (which this is — the only Python is the rodney
    smoke) follow their own toolchain. We could bump for symmetry; not
    a blocker.
  - `.twee` extension and the cookbook's substitution list. The
    cookbook AGENTS.md names `.py/.toml/.md/.json/.yaml/.yml/.txt` as
    files that get variable substitution. `.twee` isn't on that list.
    This applies to `recipes generalize` (the reverse-engineering
    tool) — it scans those extensions for variables. Cookiecutter
    itself renders all files by default, so my hand-written
    `{{ cookiecutter.X }}` markers in `.twee` files DO render
    correctly (proven by all 70 tests). Caveat: a future maintainer
    using `recipes generalize` to round-trip the template won't see
    `.twee` substitutions — flag this in the cross-repo PR's
    `notes/narrative-game-template.md`.

## Decisions

- **Twine 3 + tweego** chosen over vanilla JS / inkjs / Inform 7. tweego
  is a Go binary that ingests a directory of `.twee` files and emits a
  single self-contained HTML — no extra bundler step. The four Twine 2
  story formats it bundles (SugarCube, Harlowe, Chapbook, Snowman) are
  exposed at bake-time. SugarCube is the default; it has the macro
  vocabulary to express clicker / found-UI / choice-fiction with one
  engine. Paperthin is excluded — it is a story-format-authoring
  format, not for shipping games.
- **Three-form expressivity via crib-sheets, not template forks.** The
  baked project ships
  `examples/{dark-room,paperclips,choice-fiction}.twee` the author
  copies passages from. No `form` cookiecutter prompt. Default Start
  passage is minimal text + a single `[[Wait]]` link — works in all
  four story formats.
- **Rodney runs in the baked project's own `tests/`** rather than in
  this working. Downstream users get verification of their own
  builds; this working's `make verify` just re-runs pytest +
  regenerates charts.
- **Demo.md is hand-authored**, not showboat-built. Showboat's verify
  is whole-file all-or-nothing on fenced blocks, which doesn't fit
  a documentation file with display-only code snippets.
  Reproducibility lives in `gen_charts.sh` (charts) + the rodney
  sequence in demo.md's last section (screenshots) + the pytest
  suite (template correctness).

## Round log

| Round | Behaviour | Kind | Notes |
|------:|-----------|------|-------|
| 1 | cookiecutter.json exposes 6 prompts with documented defaults; story_format is the 4-item tweego-bundled set | red/green | 8 tests pinning prompt set, defaults, format choices |
| 2 | default bake produces 6 rendered Twee 3 source passages with no unrendered `{{` markers | red/green | 9 tests; introduced `_format_proper` mapping in cookiecutter.json |
| 3 | default bake produces buildable harness — Makefile (tweego-detection idiom), install-tweego.sh, rodney-ready test/, .gitignore | red/green | 17 tests |
| 4 | pre_gen_project rejects uppercase / hyphen-leading / spaced / punctuated slugs | red/green | RED initially asserted on `str(exc_info.value)` which doesn't carry hook stderr; amended to use `capfd` (instrumentation fix, contract unchanged) |
| 5 | blank IFID synthesises a fresh UUID4 in StoryData; user-supplied IFID preserved | red/green | post_gen_project does the synthesis (pre_gen runs before rendering, can't mutate context) |
| 6 | StoryData parses across all four format choices with canonical capitalisation | test-after | 13 tests guarding the seam between rounds 1, 2, and 5 |
| 7 | setup-twine downloads a working tweego with all 4 storyformats and is idempotent | red/green | **Real RED**: round 3 install script ended with `tweego -v` whose exit code (1, by tweego design) leaked under `set -e`. GREEN wrapped both `tweego -v` calls with `\|\| true`. |
| 8 | make dist compiles src/* into dist/index.html with `<tw-storydata name=title>` and authored content | test-after | 4 tests; network-gated |
| 9 | rodney browser smoke + end-to-end baked pipeline gate | test-after | Wires SugarCube-aware selectors (#passages .passage, a.link-internal) into the baked tests/test_smoke.py; upstream e2e test bakes → setup-twine → make dist → uv run pytest in baked project. Network + Chrome gated. |

## Final suite totals

- Default (no network): **58 passed + 12 skipped**
- `TWEEGO_NETWORK_TESTS=1`: **70 passed**

The 12 skipped at default are the network-gated rounds 7 (setup-twine,
5 tests + parametrised storyformats), 8 (dist compile, 4 tests), 9
(end-to-end e2e, 1 test) — total 12. With network gate enabled, all
70 tests pass.

## Bugs discovered along the way

1. **`tweego -v` exits 1.** Caught by round 7 RED. The `-v` flag is
   informational, but tweego's exit code reflects "did you run a
   compile?" — `-v` returns 1 because no compile happened. `set -e`
   propagated this. Fix: `"$BIN" -v || true` in install script.
2. **`<tw-passage>` is Harlowe markup, not SugarCube.** Initial
   round 9 smoke selectors targeted `<tw-passage>` (from the design
   doc); the baked SugarCube renders `#passages > .passage` with
   `data-passage` attributes. Caught immediately by running the e2e
   test. Fixed pre-commit by switching selectors and documenting the
   format-by-format selector cheat sheet in the test_smoke.py
   docstring.
3. **`addopts = "-q"` in baked pyproject suppresses test names.** The
   upstream e2e test originally asserted on individual test names in
   the captured pytest output. The `-q` setting collapses them.
   Switched the assertion to `"2 passed" in stdout`.
