# TODO — Follow-up PRs

Work items that have been scoped but deferred out of the current PR so
the in-flight branch can merge at a reviewable size. Each entry is a
standalone PR worth of work.

## CI extensions across all three cookbook templates

Add GitHub Actions workflows and `make setup-ci` targets to every
template so baked projects come with a working CI loop out of the
box. Scoped as a **v1.1 minor release** (additive across the board —
new cookiecutter variables get defaults, new Makefile targets don't
collide, new workflow files only land when opted in).

### artifact-bench

- New cookiecutter flag `include_github_workflow` (yes/no, defaults
  to `yes` — the layered verification harness only earns its keep
  when CI actually runs it).
- `.github/workflows/ci.yml`:
  - **Fast `verify` job on every PR** — `npm ci`, `make verify`,
    `make test-unit`. No browser binaries, completes in under a
    minute.
  - **Gated `e2e` job on merge to main or on-demand** — installs
    playwright with `npx playwright install --with-deps`, runs
    `make test-e2e`. ~300MB download, so keep it off the PR path.
- `make setup-ci` target: `npm ci && npx playwright install
  --with-deps`. Named differently from `make install` to make the
  extra step explicit for CI runners.
- Post-generation hook: remove `.github/` when
  `include_github_workflow=no`, matching repo-cli's existing pattern.
- Bake tests: assert the workflow file exists, splits verify from
  e2e, and uses the correct setup-ci target.

### python-project

- New cookiecutter flag `include_github_workflow` (yes/no, defaults
  to `yes`).
- `.github/workflows/ci.yml`: `uv sync --frozen`, `make test`. Single
  job, no browsers.
- `make setup-ci` target: `uv sync --frozen`. The `--frozen` flag is
  the CI-specific bit — enforces lockfile fidelity, catches drift.
- Post-generation hook: remove `.github/` when flag is `no`.
- Bake tests as above.

### repo-cli

- Extend existing `include_github_workflow` flag semantics: when
  `yes`, ship **both** `update-readme.yml` (already there) and the
  new `ci.yml`.
- `.github/workflows/ci.yml`: `uv sync --frozen`, `make test`.
- `make setup-ci` target: `uv sync --frozen`, matching python-project
  for consistency.
- Bake tests: assert both workflows land when the flag is `yes`.

## CHANGELOG reshuffle on CI landing

Once the CI work merges, reorganize `[Unreleased]` so the CI
addition and the artifact-bench template introduction sit at the top
as the premier v1.1 features. The current post-1.0.0 backfill
(status/dashboard subcommands, mypy in test gate, uv integration,
ruff rulesets, removals) should stay but shift below the headline
pair.

## npm install smoke test

A `@pytest.mark.slow` bake test that runs `npm install && make ci`
inside the baked artifact-bench output, once a Node-capable CI runner
is wired up. Currently flagged in
`cookbook/notes/artifact-bench.md`; the CI work above will unblock
this by provisioning the runner.

## `uvx showboat` demos for new templates

- `cookbook/demos/artifact-bench.md` — walks both bake variants
  (with and without the example artifact), referencing the same
  `deploy_host` the README mentions. Covered in
  `cookbook/notes/artifact-bench.md` as the immediate post-merge
  follow-up.
- Refresh `cookbook/demos/repo-cli.md` and
  `cookbook/demos/python-project.md` once they gain
  `include_github_workflow=yes` CI output so the demo reflects the
  workflow files.

## Tentative v1.1.0 release

Once the CI extensions and demo refreshes above have merged, cut the
**v1.1.0** release. The `[Unreleased]` section at that point should
carry, in the order they land on main:

1. **Added** — `artifact-bench` cookbook template (this PR)
2. **Added** — `include_github_workflow` CI flag across all three
   templates, with `setup-ci` Makefile targets
3. **Added** — `status` and `dashboard` CLI subcommands (#23), Claude
   Code GitHub Actions workflow (#27) — backfilled from post-1.0.0
   commits
4. **Changed** — `make test` runs `mypy`, uv integrated into dev
   workflow (#26, #28); `uv run` in templated Makefiles (#21);
   expanded ruff rulesets (#15); TDD discipline codified in
   `AGENTS.md` with property-enumeration requirement
5. **Removed** — `hello` CLI subcommand; `claude-code-review`
   workflow

Release steps: rename `[Unreleased]` → `[1.1.0] - YYYY-MM-DD`, open a
new empty `[Unreleased]`, bump `pyproject.toml` version, tag
`v1.1.0`, run `make dist` (which validates version ↔ tag ↔ changelog
consistency before building).
