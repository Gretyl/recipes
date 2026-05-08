# narrative-game-template notes

## Approach

The cookbook's first **interactive-fiction** template. It scaffolds a
[Twine 3](https://twinery.org/) narrative game whose Twee 3 source
passages compile to a single self-contained HTML via the
[`tweego`](https://www.motoslave.net/tweego/) Go binary. SugarCube is
the default story format; Harlowe, Chapbook, and Snowman are
selectable at bake time. The baked project ships authoring crib-sheets
for three opinionated forms — *A Dark Room*-style found-UI clickers,
*Universal Paperclips*-style numerical clickers, and IFComp-style
choice fiction — that the author copies passages from rather than
selecting via a fork-style cookiecutter prompt.

The template's only Python is the rodney browser smoke at
`tests/test_smoke.py`; the build chain itself is non-Python (tweego is
a Go binary). The Makefile follows the existing non-Python toolchain
pattern (`TOOL := $(shell command -v tool 2>/dev/null)` +
`ifdef TOOL` skip-with-warning) so a host without tweego installed
still bakes cleanly — `make setup-twine` runs `scripts/install-tweego.sh`,
which pulls tweego 2.1.1 with all four bundled storyformats into
`.tweego/` for project-local use. `make test` is the cookbook's
single pre-commit gate; here it chains `setup-twine → dist → pytest`
under rodney via sub-make calls (so each phase re-parses the Makefile
and picks up the binary `setup-twine` just installed).

The primary verification surface is **the baked project's own
`tests/`** rather than the cookbook's own test suite: a downstream
user gets headless-Chrome verification of their actual compiled
build. The cookbook root's `tests/test_bake_narrative_game_template.py`
covers the template-rendering surface (cookiecutter shape, hooks,
substitution, harness skeleton) plus a slow-marked end-to-end gate
that drives the baked `make test` when network and Chrome are
available.

## Key cookiecutter variables

- **`project_slug`** — output directory name and baked
  `pyproject.toml` `name`. Defaults to `my-narrative`. `pre_gen_project.py`
  validates it against the canonical kebab-case pattern (lowercase
  letters/digits separated by single hyphens, alphanumeric on both
  ends) and rejects with a stderr message naming the offending slug
  before any files render.
- **`title`** — the story title. Defaults to `An Untitled Room`. Threaded
  into `src/StoryTitle.twee`, which tweego reads into the
  `<tw-storydata name="...">` attribute on the compiled HTML.
- **`author_name`** — defaults to `Anonymous`. Lands in the baked
  `pyproject.toml`'s `authors` table.
- **`story_format`** — choice prompt over the four story formats
  tweego bundles: `sugarcube`, `harlowe`, `chapbook`, `snowman`. The
  fifth format tweego knows about, **paperthin**, is excluded — it's a
  story-format-authoring format, not a game-shipping format. SugarCube
  is the first choice (and therefore the default) because it has the
  macro vocabulary to express all eight mechanical primitives the three
  reference forms lean on (resource pool, action button, cooldown,
  event interrupt, upgrade, passage transition, log append, prestige);
  Harlowe and Chapbook cover middle ranges, Snowman is the most
  minimal. The lowercase prompt value maps to the canonical Twine name
  via the private `_format_proper` lookup in `cookiecutter.json` so
  StoryData renders `format: SugarCube` (not `sugarcube`).
- **`ifid`** — Twee 3 requires every story to carry an Interactive
  Fiction IDentifier (a UUID4) in StoryData. The default is the empty
  string, which signals `post_gen_project.py` to mint a fresh UUID4
  and substitute it into `src/StoryData.twee`. A user-supplied IFID is
  preserved unchanged (case included). Synthesis lives in *post*-gen
  rather than pre-gen because pre-gen runs before rendering and can't
  mutate the cookiecutter context the engine renders against.
- **`include_github_workflow`** — yes/no choice. Defaults to `yes`.
  The post-gen hook removes a `.github/` directory when the answer is
  `no`, mirroring the conditional-cleanup idiom from `repo-cli`. The
  prompt is wired to a hook ahead of the workflow file landing — the
  CI workflow itself is deferred work (see *Deferred work* below).

## Decisions and tradeoffs

- **Three-form expressivity via crib-sheets, not template forks.** The
  baked project ships `examples/{dark-room,paperclips,choice-fiction}.twee`
  the author copies passages from. There's no `form` cookiecutter
  prompt that would scaffold three different skeletons. The default
  Start passage is minimal text plus a single `[[Wait]]` link, which
  works in all four story formats — anything more opinionated would
  bias the bake away from at least one form.
- **Rodney runs in the baked project's `tests/`**, not in the
  cookbook's own test suite. The cookbook's bake-tests verify the
  template renders correctly; the baked rodney smoke verifies the
  author's actual compiled build. They guard different surfaces. The
  cookbook root carries one slow-marked end-to-end test that drives
  the baked `make test` when `TWEEGO_NETWORK_TESTS=1` and Chrome are
  available — that test is the integration gate proving template +
  hooks + install script + smoke fixtures compose into a working
  system on a real host.
- **Sub-make calls in the baked Makefile's `test:` target** rather
  than prerequisite chain. `TWEEGO := $(shell command -v tweego)`
  evaluates at parse time, so chaining `test: setup-twine dist pytest`
  as a single make invocation runs `dist` against the TWEEGO value
  detected *before* `setup-twine` populated `.tweego/` — the very
  first `make test` on a fresh host produced a stub dist and pytest
  skipped. Splitting into `$(MAKE) setup-twine; $(MAKE) dist; pytest`
  forces each sub-make to re-parse and re-detect.
- **`make test` chains setup-twine + dist + smoke.** Every other
  cookbook entry's `make test` is offline-clean. This one is online —
  it has to download tweego the first time. The trade is that a
  contributor running the cookbook-canonical pre-commit gate gets the
  full pipeline verified end-to-end without remembering a setup step;
  the cost is a one-time network hit per host and a sentinel
  `.tweego/tweego` that subsequent runs short-circuit on.
- **`addopts = "-q"` in the baked pytest config.** Trades visibility
  of individual test names for tight output on a successful smoke. The
  end-to-end test in this cookbook's bake suite asserts on the
  durable `"N passed"` summary line for that reason — test-name
  assertions would couple to the `-q` flag.

## Deferred work

- **`include_github_workflow=yes` is wired but inert.** The choice
  prompt is exposed and the post-gen hook removes a `.github/`
  directory when the answer is `no`, but the template doesn't yet
  ship a `.github/workflows/ci.yml`. Adding one would mirror
  `artifact-bench`'s `npm ci + make verify + make test-unit` flow,
  adapted to `setup-twine + make dist + make test`, plus a Mermaid
  flowchart in the baked README's `## CI` section per the cross-template
  convention `cookbook/notes/artifact-bench.md` documents.
- **`recipes generalize` doesn't scan `.twee` for substitutions.**
  The reverse-engineering tool's suffix list is `.py / .toml / .md /
  .json / .yaml / .yml / .txt`. Cookiecutter renders all files by
  default, so the hand-written `{{ cookiecutter.X }}` markers in the
  template's `.twee` files render correctly at bake time — the
  cookbook's bake suite has a sweep that confirms no Jinja tokens
  leak through. The gap is that a future maintainer using
  `recipes generalize` to round-trip an existing Twine project into a
  template won't see `.twee` files scanned for variables. Extending
  `recipes generalize` to honour `.twee` would close that loop.
- **Python 3.13 baseline parity.** The baked project targets `>=3.13`,
  matching the cookbook AGENTS.md cross-template convention. The
  template's only Python is the rodney smoke, so the bump is a
  symmetry move rather than a feature requirement; it would be
  reasonable to drop back to whatever rodney supports if a downstream
  user reports friction.

## Anti-patterns avoided

- **`tweego -v` exits with code 1.** The `-v` flag is informational —
  it prints the version string to stderr — but tweego's exit code
  reflects "did you actually run a compile?", which `-v` did not. A
  bare `"$BIN" -v` at the end of the install script propagated that
  exit 1 under `set -e` and made `scripts/install-tweego.sh` fail on
  every successful download. Wrap both `tweego -v` invocations in
  `|| true` to swallow the informational exit.
- **`<tw-passage>` is Harlowe markup, not SugarCube.** A natural
  reading of the Twine docs suggests selectors like
  `tw-passage[data-name="Start"]`, but SugarCube renders
  `#passages > .passage` with `data-passage` attributes instead. The
  baked rodney smoke's docstring carries the per-format selector
  swap table for that reason — Harlowe / Chapbook / Snowman each
  render the active passage differently, and a downstream user
  switching story formats has to swap selectors in lockstep.
- **Test-name assertions on `-q` pytest output.** `addopts = "-q"`
  collapses individual test names; assertions like
  `"test_start_passage_renders" in stdout` regress to
  green-on-everything when the flag elides them. Assert on
  `"N passed"` instead — the summary line is durable across `-q`
  and `-v`.
