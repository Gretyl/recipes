# notes-implode

Customization ledger for homing the IMPLODE v1.0 artifact into the
artifact-bench template. Every deviation from a clean template-plus-artifact
landing is recorded here, with rationale, so future sessions can tell what
was intentional vs. drift.

## Input landing map

| Source (pre-homing) | Destination | Notes |
|---|---|---|
| `input/implode.html` | `src/implode/artifact.html` | `git mv` (100% similarity) |
| `input/IMPLODE-design-bible.md` | `docs/implode/IMPLODE-design-bible.md` | `git mv` |
| `input/implode-sprite-reference.png` | `docs/implode/implode-sprite-reference.png` | `git mv`; relative link from design-bible line 10 preserved by co-location |

The `input/` directory was removed from the worktree once empty. Git does
not track empty directories, so no cleanup commit was needed.

## External references preserved

`src/implode/artifact.html` ships with four external/absolute-path
references that do **not** resolve in this repo's local bench but **do**
resolve at the production host `https://gretyl.maplecrew.org/`. The
homing decision is to keep them as-is for production parity; 404s in
local dev are benign and do not affect gameplay.

| Line | Reference | Resolves at |
|---|---|---|
| `<head>` | Google Analytics tag `G-05N3959YM1` | googletagmanager.com |
| `<head>` | `<link rel="manifest" href="/assets/manifest/implode.json">` | gretyl.maplecrew.org only |
| `<head>` | `<link rel="apple-touch-icon" href="/assets/icons/implode-180.png">` | gretyl.maplecrew.org only |
| bottom script | `navigator.serviceWorker.register('/sw-implode.js')` | gretyl.maplecrew.org only |

If you ever need self-containment (e.g., for pure copy-paste or offline
use), strip these four and record the divergence here.

## v1.0 prompt status

The v1.0 seed prompt is **unrecoverable** — the artifact shipped before
the originating prompt was preserved in this repo. The authoritative
behavioral reference going forward is `docs/implode/IMPLODE-design-bible.md`,
which documents every physics constant, state transition, depth milestone,
encounter band, and canonical drawing routine the v1.0 build exhibits.

Future iterations should append prompts to `src/implode/PROMPTS.md` and
cite specific design-bible sections they intend to change.

## Template fixes rolled up during homing

### `fix(tooling)`: html-validate config filename and button-type exemption

Two issues were surfaced by running `make verify` for the first time on
IMPLODE:

1. **Config file was being silently ignored.** html-validate 9.x
   auto-discovers `.htmlvalidate.json` (no hyphen). The template shipped
   `.html-validate.json`, so every rule override in it
   (`require-sri: off`, `no-inline-style: off`,
   `no-trailing-whitespace: off`) was being ignored — `make verify-html`
   was actually enforcing the full `html-validate:recommended` ruleset.
   Renamed to `.htmlvalidate.json` to restore discovery.
2. **`no-implicit-button-type` fired on 11 IMPLODE buttons.** IMPLODE's
   v1.0 `<button>` elements ship without explicit `type=` attributes.
   Rather than edit the shipped artifact (which would break v1.0 byte-
   for-byte fidelity), added `"no-implicit-button-type": "off"` to the
   renamed config. If a future artifact wants this rule enforced, scope
   it to that artifact's subtree rather than re-enabling globally.

Both land in the same commit since their effect is coupled (rename
alone leaves button-type firing; adding the rule alone does nothing
because the file isn't discovered).

### `fix(tooling)`: vitest `passWithNoTests: true`

Vitest's default is to exit non-zero when zero spec files match the
`include` pattern. Because this round defers test authoring to a
follow-up session, `src/implode/tests/` is empty and the hello-artifact
spec was removed — so `make test` (which CI also runs) would exit 1
purely because there's nothing to run. Added `passWithNoTests: true`
to `vitest.config.ts` so "no tests yet" is an acceptable green state.
No-op once real tests land.

## Upstream-feedback candidates

Things we added or decided downstream in this repo that the
artifact-bench template upstream could adopt so future punches don't
reinvent them.

### AGENTS.md + paired CLAUDE.md

Added a top-level `AGENTS.md` (agent-behavior guidance) and a
one-line `CLAUDE.md` containing `@AGENTS.md` (Claude Code's
file-reference syntax). Together, Claude Code picks up AGENTS.md via
CLAUDE.md without content duplication, and other agentic tools that
read `AGENTS.md` directly also work.

**Scope rule we settled on, after pushback:** AGENTS.md is for
agent-behavior guidance **only**. It is explicitly **not** a
handbook, **not** a quickstart, and does **not** restate
`docs/authoring.md` or `docs/verification.md`. Topics that belong
in repo docs stay in repo docs; AGENTS.md covers only things with
no home elsewhere.

**Sections we included** (each a concern with no pre-existing home):

- Pointer table to `docs/authoring.md`, `docs/verification.md`,
  `docs/manifest.yml`, and the `notes-<slug>.md` pattern.
- Commit & PR workflow (Conventional Commits, atomic commits,
  feature branches, commit-by-commit PR narratives).
- Per-artifact ledger convention (`notes-<slug>.md`).
- Scope discipline (don't test proactively; don't duplicate docs;
  don't touch shared surface without explicit ask).

**Sections we deliberately excluded, and why:**

| Section | Why not in AGENTS.md |
|---|---|
| Quickstart (install/verify/build/test) | `make help` target + `docs/verification.md` already cover it |
| Adding an artifact recipe | Lives in `docs/authoring.md` |
| Verification rule breakdowns | Lives in `docs/verification.md` |
| `window.storage` async-API wrinkle | Belongs in `docs/authoring.md` (which currently only teaches the localStorage-shaped API); tracked as a separate gap |

**Template adoption note:** the AGENTS.md + CLAUDE.md pair we shipped
contains no artifact-specific content — it could land in the template
verbatim so downstream repos don't reinvent the scope rule each time.

### `.gitignore` entry for `.claude/`

Claude Code stores per-session state under `.claude/`. Adding it to
`.gitignore` prevents accidental commits. Template candidate.

### README "Publishing" section

The template `README.md` had the facts about publishing split across
two places — Layout ("`public/` mirrors the deploy URLs exactly") and
Quickstart (`make build     # src/*/artifact.html -> public/`) — but
never connected them into a named flow. A reader asking "how do I
actually ship this?" had to assemble the answer themselves.

**Fix landed in this repo:** added a Publishing section to
`README.md` between Verifying changes and CI, naming `make build`
as the publish step, calling out `public/` as the deploy root with a
concrete `<slug>.html` → URL example, and noting the byte-for-byte
identity between `src/<slug>/artifact.html` and `public/<slug>.html`
so readers know the artifact file itself is the distributable.

**Template candidate:** adopt the same section upstream so every
future punch answers the publish question explicitly without a
reader having to trace through `scripts/build.ts`.

## Deferred work

### Tests not yet authored

The plan for this round was homing only; test instrumentation is a
separate follow-up session. When tests land, they need to reconcile
the storage-API mismatch below.

### window.storage API reconciliation

IMPLODE consumes the async `window.storage` surface the Claude artifact
runtime provides:

```js
const result = await window.storage.get(SCORE_KEY, true);
// result is {value: string} | null
await window.storage.set(SCORE_KEY, JSON.stringify(s), true);
```

The template's `shared/harness/storage-mock.ts` only exposes the
localStorage-shaped surface (`getItem` / `setItem`), which is what
`docs/authoring.md` teaches. Before storage-touching tests can land,
one of:

- **Extend shared `StorageMock`** with async `get` / `set` / `delete`
  methods that accept-and-ignore the second boolean arg and return
  `{value: string} | null` from `get`. Durable — future async-API
  artifacts reuse it. Recommended direction.
- **Local shim in `src/implode/tests/`** that patches
  `window.storage` before each spec. Leaves shared harness untouched.

The semantics of the second boolean arg (personal vs. shared storage,
per support.claude.com's description of the feature) is not documented
in any source I could find authoritative. The mock should accept and
ignore it unless a test wants to assert on the value.

### Canvas under jsdom

IMPLODE is canvas-heavy. `implode.html:137-138` calls
`canvas.getContext('2d')` at top-level script load. Under jsdom without
the `canvas` native dep, that returns `null` — the top-level script
still finishes (so DOM-level assertions are safe at page load), but any
render code that later dereferences `ctx.*` will throw.

Consequences for testing:
- Static/structural tests (screens present, buttons wired, initial
  DOM) work without `canvas`.
- Game-loop integration tests (advancing `startGame()` → `loop()`)
  require installing the `canvas` npm package. It's a native build
  dep; CI's ubuntu-latest ships the required libs, so `npm ci` should
  work without apt changes — but we'd be promising a compile step
  every CI run.

Decision deferred until we know which tests actually need it.

### `chore(deps)`: commit `package-lock.json` for CI continuity

The template shipped without a `package-lock.json`. CI runs `npm ci`,
which fails without a committed lockfile. Running `make install` once
locally generated the lockfile; this PR commits it so CI can install
deterministically. The dep tree pins transitive versions against the
current `package.json` contents — future dependency bumps should be
landed as separate PRs that update both `package.json` and
`package-lock.json` together.

## Known dangling items (not fixed in this PR)

### `.claude/` directory is untracked

Claude Code stores local session state under `.claude/`. Not in
`.gitignore`, but kept out of every commit in this PR by using
file-specific `git add` paths. If you want a defense in depth, add
`.claude/` to `.gitignore` in a future chore commit.
