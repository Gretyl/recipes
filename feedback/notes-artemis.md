# notes-artemis

Customization log for the homing of **Artemis Trail v1.2** into this
`artifact-bench` instance. Captures every divergence from a clean
template so future authors can replay or undo the choices.

## Homing summary

Staged inputs (now removed) lived at `input/artemis-trail.html` and
`input/artemis-trail-design-bible.md`. Homed layout:

| From | To |
|---|---|
| `input/artemis-trail.html` | `src/artemis-trail/artifact.html` (+ `// @ts-nocheck`) |
| `input/artemis-trail-design-bible.md` | `docs/artemis-trail/design-bible.md` |
| _(new)_ | `src/artemis-trail/README.md` |
| _(new)_ | `src/artemis-trail/PROMPTS.md` |
| _(new)_ | `notes-artemis.md` |

Six atomic Conventional-Commits landed the change; see `git log --oneline`.

## Artifact edits

Only one substantive edit to the source HTML:

- `src/artemis-trail/artifact.html` — prepended `// @ts-nocheck` as the
  first line of the main inline `<script>` block (just after the
  `<script>` opener that immediately follows `<div id="crt">…</div>`).

Every other byte is verbatim from `input/artemis-trail.html` as shipped
at v1.2.

## Template files modified

- `docs/manifest.yml` — replaced the commented-out `hello-artifact`
  placeholder with a live entry for `The Artemis Trail` at route
  `/artemis-trail.html`.
- `CHANGELOG.md` — recorded the homing under `[Unreleased]`.
- `src/hello-artifact/` — removed in its entirety; it was the
  template's smoke-test example and has no remaining purpose now that
  Artemis Trail is the repo's canonical artifact.

No changes to `Makefile`, `tsconfig.json`, `vitest.config.ts`,
`package.json`, `.html-validate.json`, `.github/workflows/ci.yml`, or
the `scripts/` directory. The template's artifact-discovery
(`Makefile:7`, `scripts/build.ts:44`) picks up `src/artemis-trail/`
automatically.

## Template retuning for Artemis Trail

The template ships with a `README.md` written for the generic
`cookbook/artifact-bench` recipe — "A workbench for standalone HTML
artifacts", `src/<artifact-slug>/` placeholders, a "Adding an
artifact" workflow. This repo hosts exactly one artifact, so that
framing over-indexes on capabilities we don't exercise. This pass
rewrites the README to describe the Artemis Trail instance
specifically. Landed in `docs(readme): retune for Artemis Trail
instance`.

Per-section delta (template wording → instance wording):

- **Lead paragraph:** *"A workbench for standalone HTML artifacts —
  the copy-pasteable single-file kind Claude produces — typed,
  tested, and iterated on…"* → Artemis-Trail-specific opener naming
  the game, its CRT aesthetic, and the `/artemis-trail.html` deploy
  URL.
- **`## Layout`:** generic `src/<artifact-slug>/` tree and
  `src/foo/artifact.html → public/foo.html` example → concrete tree
  showing `AGENTS.md`, `CLAUDE.md`, `README.md`, `notes-artemis.md`,
  `docs/artemis-trail/design-bible.md`, `src/artemis-trail/` and its
  real siblings; deploy-mirror sentence naming
  `artemis-trail.html` specifically.
- **`## Quickstart`:** commands unchanged. Dropped the trailing
  "Scope to one artifact: `make verify ARTIFACT=<slug>`" line —
  there's only one artifact, so the scoping feature isn't relevant
  here.
- **New `## Publishing` section** inserted between Quickstart and
  Extending. Two paragraphs: names `public/artemis-trail.html` as
  the deliverable; flags external-asset degradation (SW, PWA
  manifest, apple-touch-icon, OG image, GA) with a pointer to
  `## External asset dependencies` for the full list and the planned
  `make dist` target.
- **`## Adding an artifact` → `## Extending`:** rewritten. The
  template's "Adding an artifact" describes a workflow that happens
  rarely here; renamed and rewritten to acknowledge Artemis Trail as
  canonical, point derivatives at `docs/authoring.md`, and direct
  unrelated artifacts to their own punch-out.
- **`## Verifying changes`:** unchanged (content is intrinsically
  generic).
- **`## CI`:** unchanged except one cross-reference — line 59's
  pointer to `cookbook/notes/artifact-bench.md` (a path in the
  Gretyl/recipes repository, inaccessible from this clone) swapped
  for the local `notes-artemis.md` § "Deferred".

This retuning pass is scoped to `README.md` alone.
`docs/authoring.md` and `docs/verification.md` stay template-generic
**by design** — their content (artifact directory layout,
verify/test/build command loop) applies identically in a
single-artifact instance or a multi-artifact one, and the
instance-specific concerns that *could* live in them (the
`// @ts-nocheck` policy on the inline script, the zero-spec
`--passWithNoTests` tolerance, the deferred test-instrumentation
pass) are already captured in `notes-artemis.md` and `AGENTS.md`.
Retuning them would duplicate state and invite drift, not improve
the docs.

## External asset dependencies (forward item for `make dist`)

`artifact.html` retains the following root-relative / external
references from the Gretyl deploy. None of these assets ship in this
repo, and `make build` does not stage them into `public/`. In the
artifact-bench sandbox (opening `public/artemis-trail.html` directly),
these fetches 404 silently — the game still runs. When the artifact is
served from its Gretyl home, the hosting layer must supply them.

A future `make dist` target (or an extension of `make build`) should
stage or rewrite each of these per deploy environment:

| Reference | Location in `artifact.html` |
|---|---|
| `/sw-artemis-trail.js` | service-worker registration call |
| `/assets/manifest/artemis-trail.json` | `<link rel="manifest">` |
| `/assets/icons/artemis-trail-180.png` | `<link rel="apple-touch-icon">` |
| `https://gretyl.maplecrew.org/artemis-trail.html` | `og:url` |
| `https://gretyl.maplecrew.org/assets/og/artemis-trail.png` | `og:image` |
| `G-05N3959YM1` (Google Analytics tag) | gtag script pair near `<head>` end |

Until that target lands, **treat these as a known-tolerable
deploy-environment coupling**, not a bug.

## Type-checking observation

`make verify-types` (`Makefile:39-41`) runs plain
`npx tsc --noEmit -p tsconfig.json`, and `tsc` does not parse `.html`
files — so inline `<script>` blocks are not actually type-checked
today, despite `tsconfig.json` including `src/**/*` and the template's
hello-artifact example carrying `// @ts-check`. The `// @ts-nocheck`
pragma on `artifact.html` is therefore defensive insurance: it hurts
nothing now, and survives any future template-level change that
introduces an HTML-script extraction step.

A JSDoc retrofit on Artemis Trail's inline script, paired with real
type-checking of extracted logic, belongs in the test-instrumentation
follow-up.

## Deferred

The following are intentionally **not** part of this homing pass:

- Unit tests (`src/artemis-trail/tests/unit.spec.ts`) — requires first
  extracting the pure game helpers (`clamp`, `fx`, `pick`, `pv`,
  `fmtFx`, `isCritical`, the event-selection probability math) out of
  DOM-mutating callsites like `advance()`.
- Integration tests — deferred alongside the v1.2 rodney-based e2e
  return that the template README flags.
- JSDoc retrofit (see "Type-checking observation" above).
- `make dist` (or asset-staging extension to `make build`) — see
  "External asset dependencies" above.

## Upstream feedback — `cookbook/artifact-bench` (Gretyl/recipes)

Items to file back against the template recipe next time we're in
Gretyl/recipes. These are not specific to Artemis Trail; they're
artifact-bench-wide gaps surfaced during this homing.

### Pin a `package-lock.json` at the template level

`.github/workflows/ci.yml:32` runs `npm ci`, which requires a lockfile
and fails loudly if `package.json` and `package-lock.json` drift. But
the template's punch-out produces no lockfile — so every freshly-
instantiated artifact-bench repo's first CI run fails until someone
runs `make install` and commits the result.

Two ways to fix upstream, equivalent in effect:

1. **Ship the lockfile in the recipe.** Commit `package-lock.json`
   alongside `package.json` in `cookbook/artifact-bench`. Every
   punch-out inherits the same, reviewed dep tree.
2. **Have the punch tool generate one.** If the cookbook punch flow
   runs `npm install` as part of instantiation, commit the resulting
   lockfile before finalizing the new repo.

Option 1 is simpler and has the added benefit of making the template
itself reproducible — every punch-out starts from the exact same
versions of `tsc`, `vitest`, `jsdom`, `html-validate`, etc. This
repo's locally-landed `package-lock.json` (commit `e2eefc9`) can
serve as reference.

### Make `make test` tolerate the zero-specs window

`make test` invokes `npx vitest run` without `--passWithNoTests`, so
it exits 1 whenever no spec files exist — e.g., the window between
removing a template example's tests and authoring the first real
artifact's tests (exactly where this repo sat after commit `cdb6d3c`
and before the forthcoming test-instrumentation pass). The template
should either pass `--passWithNoTests` in `Makefile:53` or ship every
new artifact with a smoke-test stub so the red interval is measured
in minutes, not days.

**Patched locally in commit `fe83887`** (`fix(ci): tolerate empty
vitest spec set in make test-unit`). The `test-unit` target now
invokes `npx vitest run --passWithNoTests $(SCOPE)`, returning
exit 0 with a "No test files found" note when the spec set is
empty. Upstream `cookbook/artifact-bench` should adopt this
one-flag change (or the smoke-test-stub alternative).

### Ship agent-metadata scaffolding by default

`cookbook/artifact-bench` currently ships no `AGENTS.md`, no
`CLAUDE.md`, and no `.gitignore` entry for `.claude/`. Each
punch-out rediscovers the same agent-facing conventions (commit
style, TDD stance, tests layout, etiquette) or skips them
entirely. Three small additions to the recipe fix this once for
every future instance:

1. **`AGENTS.md` at repo root** with agent-only scope —
   orientation pointers into `README.md`, `docs/authoring.md`,
   `docs/verification.md`, plus handbook content for conventions
   that have no other home (commits, TDD applicability, tests
   layout, file-edit etiquette, skills/tooling). Keeps agent
   guidance from duplicating human-audience docs.
2. **`CLAUDE.md` one-liner** containing `@AGENTS.md`. Canonical
   delegation stub — any Claude-specific tooling reads `CLAUDE.md`
   and is silently forwarded to the tool-agnostic handbook.
3. **`.claude/` in `.gitignore`** so Claude Code's per-project
   session state (settings, hook overrides, slash-command drafts)
   never leaks into commits.

**Landed locally** in commits `1c7d789` (`chore: gitignore
.claude/`) and `d993810` (`docs: init AGENTS.md handbook and
CLAUDE.md delegation stub`). Both are close to lift-and-shift for
the template; the upstream `AGENTS.md` needs small edits where
this repo's version names Artemis Trail as the canonical artifact
— the template version should point at the "home your first
artifact" authoring flow instead.

### Tune template README toward instance-faithful framing

The template's `README.md` reads as a generic multi-artifact
workbench intro. Each punch-out — including this one — ships with
that framing intact even when the instance hosts exactly one
artifact, forcing every future reader to filter template-leftover
guidance from instance-relevant content. Two small template
changes would reduce the retuning burden:

1. **Ship a `<!-- INSTANCE: … -->` placeholder line in the template
   `README.md`** that the punch tool fills in on instantiation
   (artifact title, deploy URL, design-bible path). Makes the top
   of the file instance-faithful from day one with zero authoring
   work at punch time.
2. **Hoist the generic "Adding an artifact" section out of the
   template `README.md` into `docs/authoring.md`.** The detailed
   how-to already lives there; keeping a one-paragraph copy at the
   README top level forces single-artifact instances to rewrite it
   into something more appropriate (`## Extending`, in this
   repo's retune). If the section isn't there to begin with,
   instance READMEs don't need to rewrite it.

**Landed locally** in `docs(readme): retune for Artemis Trail
instance`, with a per-section diff cataloged in
[`## Template retuning for Artemis Trail`](#template-retuning-for-artemis-trail)
above. That commit's `README.md` is a concrete exemplar of what a
post-retune instance README looks like; upstream can diff it
against the template to see the per-change surface area.
