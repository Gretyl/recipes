# `narrative-game-template`

A cookiecutter template that scaffolds **Twine 3 narrative-game
projects** — Twee 3 source passages compiled to a single
self-contained HTML by the `tweego` Go binary, with SugarCube as the
default story format and bundled crib-sheets for three opinionated
forms (*A Dark Room*-style found-UI clicker, *Universal Paperclips*-
style numerical clicker, IFComp-style choice fiction).

The directory layout is **flat at the working root**
(`cookiecutter.json`, `hooks/`, `{{cookiecutter.project_slug}}/`)
to match Gretyl/recipes' `cookbook/<entry>/` convention — drop the
working contents into `cookbook/narrative-game-template/` and the
template is integration-ready. This working built and red/green-tested
it inside grimoire so the design is anchored against existing repo
conventions (`repo-cli`'s cookiecutter shape,
`evolution-trust-simulations`' toolchain-detect Makefile idiom,
grimoire's `docs/non-python-toolchains.md`, `docs/demo-validation.md`,
and `docs/distribution.md`'s browser smoke recipes).

## Outcome

Default suite (no network): **58 passed + 12 skipped**.
With `TWEEGO_NETWORK_TESTS=1`: **70 passed**.

The template lives at `template/`. A no-input bake produces a
project that:

- includes six Twee 3 source passages (StoryData, StoryTitle,
  StoryStylesheet, StoryScript, StoryInit, Start) with a fresh UUID4
  IFID synthesised at bake time;
- has a Makefile with `setup-twine`, `dist`, `verify`, `clean`
  targets that detect tweego and skip cleanly when absent;
- ships an idempotent platform-aware `scripts/install-tweego.sh`
  that downloads tweego 2.1.1 from the GitHub mirror and bundles all
  four Twine 2 story formats (SugarCube, Harlowe, Chapbook, Snowman);
- includes a rodney browser smoke (`tests/test_smoke.py`) that
  drives headless Chrome against the compiled HTML and asserts the
  start passage renders + the first link transitions;
- ships authoring crib-sheets at `examples/{dark-room,paperclips,
  choice-fiction}.twee` — explicitly *not* compiled by the default
  build, available for the author to copy passages from.

See [`demo.md`](demo.md) for the showboat-verified walkthrough,
including rendered screenshots of all three forms.

## Layout

```
narrative-game-template/
├── AGENTS.md            # working-local TDD/bake checklist
├── README.md            # this file
├── notes.md             # round log + decisions
├── demo.md              # showboat-built walkthrough w/ screenshots
├── Makefile             # working-level: test / bake / verify / clean
├── pyproject.toml       # cookiecutter, pytest, rodney, chartroom, showboat
├── data/                # CSVs feeding the chartroom artefacts
├── charts/              # design-rationale PNGs + rendered screenshots
├── gen_charts.sh        # regenerate charts/ from data/
├── tests/               # PRE-bake pytest (template source)
│
│  # ---- the cookiecutter entry root (flat, cookbook-shaped) ----
├── cookiecutter.json
├── hooks/
│   ├── pre_gen_project.py     # slug validation
│   └── post_gen_project.py    # IFID synthesis + .github/ pruning
└── {{cookiecutter.project_slug}}/
    ├── README.md
    ├── Makefile                  # tweego detect / setup-twine / dist / test
    ├── pyproject.toml             # rodney + pytest dev deps
    ├── .gitignore                 # dist/, .tweego/, .rodney/
    ├── scripts/install-tweego.sh
    ├── src/                       # Twee 3 source consumed by tweego
    │   ├── StoryData.twee
    │   ├── StoryTitle.twee
    │   ├── StoryStylesheet.twee
    │   ├── StoryScript.twee
    │   ├── StoryInit.twee
    │   └── Start.twee
    ├── examples/                  # crib-sheets — NOT in tweego's input
    │   ├── README.md
    │   ├── dark-room.twee
    │   ├── paperclips.twee
    │   └── choice-fiction.twee
    └── tests/
        ├── conftest.py
        └── test_smoke.py          # rodney drive
```

When migrating to `Gretyl/recipes`, only the cookiecutter entry root
(`cookiecutter.json` + `hooks/` + `{{cookiecutter.project_slug}}/`)
moves into `cookbook/narrative-game-template/`. The working metadata
(AGENTS.md, README, notes, demo, charts, data, gen_charts.sh, tests)
maps to:

  - `cookbook/notes/narrative-game-template.md` ← this working's notes.md
  - `cookbook/demos/narrative-game-template.md` ← this working's demo.md
  - `tests/test_bake_narrative_game_template.py` ← the union of this
    working's tests/test_*.py (consolidated per cookbook convention)
  - `cookbook/charts/narrative-game-template/` ← this working's charts/
    (or wherever the cookbook houses chart artefacts)

## Working: development workflow

```bash
make test                          # pytest (pre-bake + bake-then-post-bake)
make bake                          # cookiecutter into /tmp/baked-narrative-default
make verify                        # showboat verify demo.md
TWEEGO_NETWORK_TESTS=1 make test   # plus network-gated rounds 7-9
```

## Reuse from grimoire

Read-only references that shaped this working's design:

- `repo-cli/template/` — cookiecutter directory shape and post_gen
  hook idiom (conditional `.github/` removal). See round 5 GREEN.
- `evolution-trust-simulations/Makefile` — `TOOL := $(shell command
  -v tool 2>/dev/null)` + `ifdef TOOL` skip-with-warning pattern.
  See the baked Makefile.
- `docs/non-python-toolchains.md` — drives the `setup-twine`
  target shape and `scripts/install-tweego.sh` semantics.
- `docs/demo-validation.md` + `docs/distribution.md` browser smoke
  test — drives `gen_charts.sh`, the chart filenames, and the
  rodney sequence baked into `tests/test_smoke.py`.

What is *not* reused:

- `scripts/bundle-standalone-html.mjs` — tweego already emits a
  self-contained HTML; no module-inlining step is needed.
- `evolution-trust-simulations/test/bundle.test.js` (DOM-stubbed
  vm) — there are no ES modules in the Twine output to vm-execute;
  the right test surface is rodney against the rendered HTML.

## Cross-repo PR (out of scope here)

Contributing the template into Gretyl/recipes' `cookbook/` is
follow-up work after this working merges to grimoire's `main`. The
working's commit log preserves the per-round red/green progression
that drove the design; squash-merge to main is expected, with
`notes.md` carrying the colour into the cookbook PR.
