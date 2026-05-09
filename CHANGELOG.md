# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `python-project`: template now ships a `CLAUDE.md` delegation stub at the project root (`@AGENTS.md`) so agents that look up `CLAUDE.md` first reach the same guidance as those that read `AGENTS.md`. Matches the `artifact-bench` pattern. `repo-cli` deliberately does not ship a `CLAUDE.md` — it's designed to bake into a host repo as a subpackage, and the host's project-root file belongs to the host.
- `python-project` and `repo-cli`: baked `AGENTS.md` now includes a Commit Conventions section naming Conventional Commits, listing the parent repo's allowed types (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`), and template-appropriate scopes (`lib` / `cli`, plus `tests`, `docs`, `deps`). A fresh punch can now follow the convention without chasing it back to the parent repo.
- `python-project`: baked `AGENTS.md` now documents the release sequence (bump `pyproject.toml` → rename `[Unreleased]` → `uv sync` *before* commit → `chore(release):` commit → annotated `git tag -a` → `make dist` validates → push). Condenses `/AGENTS.md` § "Distribution" so a fresh punch carries the discipline inline; the baked Makefile already ships the `make dist` validation gate but the order to run things wasn't reachable without the parent repo.
- `repo-cli`: baked `AGENTS.md` now warns that edits inside `README.md`'s Cog blocks (`<!--[[[cog ... ]]]-->`) are silently overwritten on every push to `main` by `update-readme.yml`'s `cog -r README.md` run, with `{{cookiecutter.package_name}}/tui/template.py` named as the canonical edit site. The template-management subcommands and Cog-based README pipeline existed in the bake but the overwrite hazard wasn't documented.
- `artifact-bench`: baked `AGENTS.md` now names the three cookiecutter variables that are baked at punch time and govern parts of the layout an agent can't flip post-bake: `primary_artifact_slug`, `include_example_artifact`, `include_github_workflows`. Frames them as integration commitments, not runtime config.
- `artifact-bench`: template now ships `AGENTS.md` (agent-only scope, per the convention IMPLODE's homing documented — no duplication of `docs/authoring.md` or `docs/verification.md`) and a `CLAUDE.md` delegation stub (`@AGENTS.md`), so every punch inherits the commit workflow, per-artifact-ledger pattern, and scope-discipline guidance without rediscovering them.
- `artifact-bench`: template now ships `package-lock.json`, making `npm ci` succeed on first CI run instead of failing until an author locally regenerates and commits the lockfile.
- `artifact-bench`: README now has a `## Publishing` section explicitly naming `make build` as the publish step, the byte-for-byte `src/<slug>/artifact.html → public/<slug>.html` identity, and the deploy URL. Both Artemis Trail and IMPLODE arrived at near-identical prose for this independently during their homings.
- `artifact-bench`: new `primary_artifact_slug` cookiecutter variable (default empty). When set, the README opens with a `Hosting **<title>** as the canonical artifact...` block that names the canonical artifact and threads the slug into the deploy URL, replacing the generic multi-artifact lead. Empty default preserves the current generic framing. Title is derived from the slug via Jinja (`| replace('-', ' ') | title`), no second variable required.

### Fixed

- `python-project` and `repo-cli`: baked `AGENTS.md` PR-body convention now matches `/AGENTS.md` ("write the PR body as a narrative summary of what changed and why — not a commit list"). Both templates previously instructed authors to *list every commit in-order as the PR body*, which contradicted the parent repo and meant punched-out projects inherited opposite advice depending on which template they came from. `artifact-bench` already followed the parent.
- `artifact-bench`: renamed `.html-validate.json` → `.htmlvalidate.json`. html-validate 9.x auto-discovers the non-hyphenated name only, so the template's rule overrides (`require-sri: off`, `no-inline-style: off`, `no-trailing-whitespace: off`) were being silently ignored on every punch — `make verify-html` was actually enforcing the full `html-validate:recommended` ruleset. Also added `no-implicit-button-type: off` since Claude-produced `<button>` elements routinely omit explicit `type=`.
- `artifact-bench`: `make test-unit` now tolerates an empty spec set (`passWithNoTests: true` in `vitest.config.ts`) — previously the Makefile gate failed whenever an artifact existed without tests, which is the explicit "add tests when a regression demands it" state `docs/verification.md` documents.
- `artifact-bench`: `make verify-html` now short-circuits to `ok` when `src/` is empty instead of erroring on html-validate's "no files matching patterns" diagnostic. Companion to the vitest empty-tolerance fix above — a fresh punch with no artifacts is a legitimate green state.
- `artifact-bench`: dropped the dead `cookbook/notes/artifact-bench.md` cross-reference from the baked README and `.github/workflows/ci.yml` header comment — that path exists in the Gretyl/recipes source repo, not in punched-out instances.
- `artifact-bench`: hoisted the one-paragraph `## Adding an artifact` section out of the baked README into `docs/authoring.md` only (the section `## Adding one` there already holds the full flow). Both Artemis Trail and IMPLODE retuned or dropped this paragraph in their instance READMEs because the generic phrasing doesn't fit single-canonical-artifact instances.

### Changed

- Release process: tags are now mandated to be **annotated** (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`) per `AGENTS.md` § "Distribution". Lightweight tags strand the tagger identity, timestamp, and message that `git describe`, `git log --decorate`, and the GitHub release UI all read; the published `v1.1.0` is the existing cautionary example, and the immutability rule on the git server makes a stranded lightweight tag unrecoverable except by issuing a new patch version.
- `artifact-bench`: `.gitignore` now excludes `.claude/` so Claude Code's per-project session state doesn't leak into commits.

## [1.1.1] - 2026-04-19

### Fixed

- `uv.lock` now matches `pyproject.toml` for the v1.1.x release. v1.1.0's release commit bumped `pyproject.toml` to 1.1.0 but shipped an unchanged lockfile from v1.0.0, so `uv sync --frozen` failed against the tagged state. The git server refused to reassign the v1.1.0 tag, so this patch release is the published fix — consumers should prefer v1.1.1 over v1.1.0.

## [1.1.0] - 2026-04-19

### Added

- Initial `artifact-bench` cookbook template for HTML-artifact workbenches (Node/TypeScript; layered verification harness covering structure, tsc `--checkJs`, html-validate, and vitest/jsdom unit tests; optional example artifact). Browser-level e2e is planned for v1.2 via a lightweight rodney-based replacement — see `cookbook/notes/artifact-bench.md` "Deferred work".
- `include_github_workflows` cookiecutter flag across all three cookbook templates. When `yes`, bakes a `.github/workflows/ci.yml`. For `python-project` and `repo-cli`, `ci.yml` runs `make setup-ci && make test` (with `setup-ci` doing `uv sync --frozen`); `repo-cli` continues to gate the existing `update-readme.yml` alongside the new `ci.yml`. For `artifact-bench`, `ci.yml` runs `npm ci` + `make verify` (structure + tsc `--checkJs` + html-validate) + `make test-unit` (vitest/jsdom). Baked projects include a `## CI` README section with a Mermaid flowchart documenting the trigger-to-step path.
- `status` and `dashboard` CLI subcommands using Rich and Textual.  #23
- Claude Code GitHub Actions workflow.  #27

### Changed

- Renamed `repo-cli`'s `include_github_workflow` cookiecutter flag to `include_github_workflows` (plural) to reflect that it now gates multiple workflow files. Scripted bakes that pass the flag via `--extra-context` must update the key name; already-baked projects are unaffected.
- `make test` now runs `mypy` as part of the gate; uv integrated into the development workflow.  #26, #28
- Makefiles use `uv run` to execute Python tools.  #21
- Template ships with ruff rulesets SIM, PIE, RET, C90, C4, N, PLW, PLC enabled.  #15
- Codified TDD discipline in `AGENTS.md`: red→green pairs, property-enumeration requirement (behavior/propagation/inverse-branch/sweep) before commit #1, and behavior-over-module naming for `test(...)` subjects.

### Removed

- `hello` subcommand from the recipes CLI.
- `claude-code-review` GitHub Actions workflow.

## [1.0.0] - 2026-02-13

### Added

- Templated `make dist` target for `python-project` cookbook.  #10
- `generalize` and `meld makefiles` CLI subcommands.  #9
- Bake-level tests for `python-project` template.  #9

### Fixed

- Template Makefile and mypy issues in `python-project`; v1.0 quality pass.  #9

### Changed

- Migrated project instructions to `AGENTS.md`.
- Removed `scripts/*.py` from `python-project` template output.

## [0.9.0] - 2026-02-13

### Added

- Template extension: `template.py` with `apply` and `prepare` subcommands for Cog-based README management.
- GitHub Actions workflow option (`include_github_workflow`) with `update-readme.yml`.
- Post-generation hook to conditionally remove `.github/` directory.
- 54 template-level tests in baked output (test_template, test_template_apply, test_template_prepare).
- First bake-level test suite (`tests/test_bake_repo_cli.py`).

## [0.1.0] - 2026-02-04

### Added

- Initial release of Recipes CLI.
