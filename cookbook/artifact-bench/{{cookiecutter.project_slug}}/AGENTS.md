# AGENTS.md

Agent-behavior guidance for this workbench. This file is scoped to
conventions that have no other home — it is **not** a quickstart, **not**
a handbook, and does **not** restate `docs/authoring.md` or
`docs/verification.md`. If a topic belongs in repo docs, it stays in repo
docs.

## Where things live

| Topic | File |
|-------|------|
| What this repo is + deploy layout + Quickstart | `README.md` |
| How to add your first artifact | `docs/authoring.md` (§ "Adding one") |
| What `make verify` / `make test` cover and when to add tests | `docs/verification.md` |
| Gallery entries (drives `public/index.html`) | `docs/manifest.yml` |
| Per-artifact decision ledger | `notes-<slug>.md` at repo root (one per artifact homing) |

Run `make help` for the target list; don't duplicate it here.

## Commit & PR workflow

- **Conventional Commits** on the subject line: `<type>(<scope>): <summary>`.
  Types in use: `feat`, `fix`, `docs`, `style`, `refactor`, `test`,
  `chore`, `build`, `ci`, `perf`. Scopes that make sense here:
  `template`, `artifact`, `tooling`, `ci`, `docs`, `deps`.
- **Atomic commits.** One logical change per commit. Tests and the
  implementation they drive land as separate commits so the red→green
  transition is observable in `git log`.
- **Feature branches**, not commits-on-`main`. Push to a topic branch
  and open a PR.
- **Narrative PR bodies.** The PR title summarizes the branch; the body
  is a short narrative of what changed and why. Do **not** paste the
  commit list into the body — GitHub already shows it.

## Per-artifact ledger: `notes-<slug>.md`

When you home an artifact into this workbench (or iterate on one), keep
a customization ledger at the repo root: `notes-<artifact-slug>.md`.
Record every divergence from a clean template + artifact landing —
template files modified, artifact edits, deferred work, external
dependencies — with enough context that a future session can tell
intentional choices from drift.

## Scope discipline

- **Don't add tests proactively.** Follow `docs/verification.md`'s
  floor: an artifact without `README.md` and `PROMPTS.md` won't land.
  Tests land the first time you catch a regression you wish you'd
  caught automatically.
- **Don't duplicate docs.** If you find yourself explaining the same
  thing in two places, keep it in the doc it belongs to and link from
  the other.
- **Don't touch shared surface without an explicit ask.**
  `shared/harness/`, `shared/types/`, `scripts/`, the root `Makefile`,
  and `cookiecutter.json`-sourced files belong to the template; edits
  that affect every punch go through a template change, not a
  per-instance patch. Per-artifact fixes go in the artifact's subtree.

## Empty-repo green is intentional

A fresh punch with no artifacts will pass `make verify && make
test-unit && make build` trivially — there's nothing to verify, no
specs to run, nothing to build. That's the intended state, not a signal
that CI is broken. Land your first artifact before expecting meaningful
signal from the gate.

## File-edit etiquette

- Prefer editing existing files to creating new ones. A per-artifact
  `notes-<slug>.md` or a new spec under `src/<slug>/tests/` is fine;
  adding a sibling to `docs/` or a new top-level file usually isn't.
- When renaming or moving files, use `git mv` so rename detection
  survives in history.
- Keep artifacts byte-identical to the shipped Claude output where
  possible. If you must edit `artifact.html`, record the edit and its
  rationale in the ledger.
