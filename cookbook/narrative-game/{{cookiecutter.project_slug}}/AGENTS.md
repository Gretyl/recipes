# AGENTS.md

Agent-behavior guidance for this Twine narrative game. Scoped to
conventions that have no other home — the `README.md` is the
user-facing quickstart; this file pins the "what an agent should know
that the README doesn't tell them" surface.

## Where things live

| Topic | File |
|-------|------|
| Quickstart, layout, build chain | `README.md` |
| Twee 3 source (compiled into `dist/index.html`) | `src/*.twee` |
| Authoring crib-sheets (NOT compiled) | `examples/{dark-room,paperclips,choice-fiction}.twee` |
| Browser smoke (rodney + headless Chrome) | `tests/test_smoke.py` |
| Tweego installer (project-local fallback) | `scripts/install-tweego.sh` |

`tweego` walks `src/` only. Treat `examples/` as the reference shelf —
copy passages out of it into `src/` to use a recipe; never put
authoring material under `src/` that you don't want compiled.

## Punch knobs

Three cookiecutter variables are baked at punch time and govern parts
of the layout you can't flip later without re-baking:

- **`story_format`** — one of `sugarcube` (default), `harlowe`,
  `chapbook`, or `snowman`. Threads through `src/StoryData.twee` (via
  the `_format_proper` private lookup that maps lowercase → CamelCase
  Twine name), the README header, and the rodney smoke's per-format
  DOM-selector branch (SugarCube → `#passages .passage` /
  `a.link-internal`; Harlowe → `tw-passage` / `tw-link`; Chapbook →
  `.page` / `.page a`; Snowman → `#story` / `#story a`). To switch
  formats post-bake, re-bake — a hand-edit must update every site or
  the smoke fails.
- **`ifid`** — the Interactive Fiction IDentifier required by Twee 3.
  Empty default triggers `post_gen_project.py` to mint a fresh UUID4
  and substitute it into `src/StoryData.twee`; a user-supplied IFID is
  preserved unchanged (case included). Don't delete the post-gen
  hook — the empty default depends on it.
- **`include_github_workflow`** — yes/no choice. The post-gen hook
  removes `.github/` when the answer is `no`; the workflow file
  itself is deferred work, so the yes-branch ships nothing yet.

## Build chain

`make test` is the pre-commit gate. It chains
`setup-twine → dist → pytest` via **sub-make calls**, not
prerequisites — `TWEEGO := $(shell command -v tweego)` evaluates at
parse time, so a single `make` invocation can't see binaries that
`setup-twine` created. If you "tidy" the Makefile to
`test: setup-twine dist pytest`, the very first run produces a stub
dist and pytest skips silently.

`make setup-twine` is **online-first** on first invocation: it
downloads tweego 2.1.1 with all four bundled story formats into
`.tweego/`. Subsequent runs short-circuit on the `.tweego/tweego`
sentinel. CI in a sandbox without network access must either
pre-populate `.tweego/` or accept the skip.

`Start.twee` is intentionally minimal (text + one `[[Wait]]` link) so
it compiles under all four story formats. Anything more opinionated
biases the bake away from at least one format — branch out from
`examples/` instead of editing Start with format-specific macros.

## Commit & PR workflow

- **Conventional Commits** on the subject line: `<type>(<scope>):
  <summary>`. Types in use: `feat`, `fix`, `docs`, `style`,
  `refactor`, `test`, `chore`, `build`, `ci`, `perf`. Scopes that
  make sense here: `story` (`src/*.twee` content), `build`
  (`Makefile`, `scripts/install-tweego.sh`, tweego), `test`
  (smoke, rodney, conftest), `docs` (`README.md`, this file).
- **PR bodies are narrative**, not a commit list. Summarize *what*
  changed and *why*; GitHub already surfaces the commit log, and
  duplicating it is noise during review.
