# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial `narrative-game` cookbook template for Twine 3 narrative games. Baked projects scaffold a Twee 3 source tree (`StoryData`, `StoryTitle`, `StoryStylesheet`, `StoryScript`, `StoryInit`, `Start`) compiled to a single self-contained HTML by the `tweego` Go binary; SugarCube is the default story format with Harlowe, Chapbook, and Snowman selectable. The bake includes authoring crib-sheets at `examples/{dark-room,paperclips,choice-fiction}.twee` for *A Dark Room*-style found-UI clickers, *Universal Paperclips*-style numerical clickers, and IFComp-style choice fiction. The baked Makefile detects system tweego with `setup-twine` falling back to a project-local install via `scripts/install-tweego.sh` (idempotent, platform-aware via `uname`); `make test` chains `setup-twine → dist → pytest` under a rodney-driven headless-Chrome smoke. `post_gen_project.py` mints a fresh UUID4 IFID when the cookiecutter prompt is left blank. Walkthrough with screenshots in `cookbook/demos/narrative-game.md`; design notes in `cookbook/notes/narrative-game.md`.
- `narrative-game`: template now ships an `AGENTS.md` at the project root (scoped to agent-only conventions) and a `CLAUDE.md` delegation stub (`@AGENTS.md`), bringing the fourth cookbook entry into parity with `python-project` and `artifact-bench`. The baked AGENTS.md documents Twee 3 source layout, the three baked-at-punch-time cookiecutter variables (`story_format`, `ifid`, `include_github_workflow`), the build chain's parse-time TWEEGO-detection hazard requiring sub-make calls in `make test`, and Conventional Commits with template-appropriate scopes (`story`, `build`, `test`, `docs`).
- `narrative-game`: bake now ships `tests/test_source.py` with three always-on static checks against the Twee 3 source (StoryData passage header, non-empty IFID, Start passage header). Ensures a punched-out project produces non-zero passing tests in any environment, even when the Chrome+tweego prerequisites for `tests/test_smoke.py` are absent — meets the new "representative coverage out of the box" expectation for Python-bearing templates.
- `python-project`: template now ships a `CLAUDE.md` delegation stub at the project root (`@AGENTS.md`) so agents that look up `CLAUDE.md` first reach the same guidance as those that read `AGENTS.md`. Matches the `artifact-bench` pattern. `repo-cli` deliberately does not ship a `CLAUDE.md` — it's designed to bake into a host repo as a subpackage, and the host's project-root file belongs to the host.
- `python-project` and `repo-cli`: baked `AGENTS.md` now includes a Commit Conventions section naming Conventional Commits, listing the parent repo's allowed types (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`), and template-appropriate scopes (`lib` / `cli`, plus `tests`, `docs`, `deps`). A fresh punch can now follow the convention without chasing it back to the parent repo.
- `python-project`: baked `AGENTS.md` now documents the release sequence (bump `pyproject.toml` → rename `[Unreleased]` → `uv sync` *before* commit → `chore(release):` commit → annotated `git tag -a` → `make dist` validates → push). Condenses `/docs/RELEASE.md` so a fresh punch carries the discipline inline; the baked Makefile already ships the `make dist` validation gate but the order to run things wasn't reachable without the parent repo.
- `repo-cli`: baked `AGENTS.md` now warns that edits inside `README.md`'s Cog blocks (`<!--[[[cog ... ]]]-->`) are silently overwritten on every push to `main` by `update-readme.yml`'s `cog -r README.md` run, with `{{cookiecutter.package_name}}/tui/template.py` named as the canonical edit site. The template-management subcommands and Cog-based README pipeline existed in the bake but the overwrite hazard wasn't documented.
- `artifact-bench`: baked `AGENTS.md` now names the three cookiecutter variables that are baked at punch time and govern parts of the layout an agent can't flip post-bake: `primary_artifact_slug`, `include_example_artifact`, `include_github_workflows`. Frames them as integration commitments, not runtime config.
- `artifact-bench`: template now ships `AGENTS.md` (agent-only scope, per the convention IMPLODE's homing documented — no duplication of `docs/authoring.md` or `docs/verification.md`) and a `CLAUDE.md` delegation stub (`@AGENTS.md`), so every punch inherits the commit workflow, per-artifact-ledger pattern, and scope-discipline guidance without rediscovering them.
- `artifact-bench`: template now ships `package-lock.json`, making `npm ci` succeed on first CI run instead of failing until an author locally regenerates and commits the lockfile.
- `artifact-bench`: README now has a `## Publishing` section explicitly naming `make build` as the publish step, the byte-for-byte `src/<slug>/artifact.html → public/<slug>.html` identity, and the deploy URL. Both Artemis Trail and IMPLODE arrived at near-identical prose for this independently during their homings.
- `artifact-bench`: new `primary_artifact_slug` cookiecutter variable (default empty). When set, the README opens with a `Hosting **<title>** as the canonical artifact...` block that names the canonical artifact and threads the slug into the deploy URL, replacing the generic multi-artifact lead. Empty default preserves the current generic framing. Title is derived from the slug via Jinja (`| replace('-', ' ') | title`), no second variable required.
- `pyproject.toml`: added `[tool.uv]` section with `exclude-newer` pinning uv's resolution window to packages published at least seven days ago. Guards against yanks, supply-chain rushes, and accidental publishes by excluding very-recently-published versions from new resolutions. Adding the constraint triggered a fresh resolution that bumped `binaryornot 0.4.4 → 0.6.0` (drops the now-unused `chardet` transitive), `certifi 2026.1.4 → 2026.4.22`, and `charset-normalizer 3.4.4 → 3.4.7`. The release checklist now requires this setting to be present before any `uv` command runs in the release sequence.

### Fixed

- `python-project` and `repo-cli`: baked `AGENTS.md` PR-body convention now matches `/AGENTS.md` ("write the PR body as a narrative summary of what changed and why — not a commit list"). Both templates previously instructed authors to *list every commit in-order as the PR body*, which contradicted the parent repo and meant punched-out projects inherited opposite advice depending on which template they came from. `artifact-bench` already followed the parent.
- `artifact-bench`: renamed `.html-validate.json` → `.htmlvalidate.json`. html-validate 9.x auto-discovers the non-hyphenated name only, so the template's rule overrides (`require-sri: off`, `no-inline-style: off`, `no-trailing-whitespace: off`) were being silently ignored on every punch — `make verify-html` was actually enforcing the full `html-validate:recommended` ruleset. Also added `no-implicit-button-type: off` since Claude-produced `<button>` elements routinely omit explicit `type=`.
- `artifact-bench`: `make test-unit` now tolerates an empty spec set (`passWithNoTests: true` in `vitest.config.ts`) — previously the Makefile gate failed whenever an artifact existed without tests, which is the explicit "add tests when a regression demands it" state `docs/verification.md` documents.
- `artifact-bench`: `make verify-html` now short-circuits to `ok` when `src/` is empty instead of erroring on html-validate's "no files matching patterns" diagnostic. Companion to the vitest empty-tolerance fix above — a fresh punch with no artifacts is a legitimate green state.
- `artifact-bench`: dropped the dead `cookbook/notes/artifact-bench.md` cross-reference from the baked README and `.github/workflows/ci.yml` header comment — that path exists in the Gretyl/recipes source repo, not in punched-out instances.
- `artifact-bench`: hoisted the one-paragraph `## Adding an artifact` section out of the baked README into `docs/authoring.md` only (the section `## Adding one` there already holds the full flow). Both Artemis Trail and IMPLODE retuned or dropped this paragraph in their instance READMEs because the generic phrasing doesn't fit single-canonical-artifact instances.

### Changed

- Per-template agent guidance is now enforced by a discovery-based MVP contract in `tests/test_template_consistency.py::TestPerTemplateAgentGuidance` instead of hardcoded per-template parametrize rows. The sweep enumerates every directory under `cookbook/` containing a `cookiecutter.json` and applies three properties to each: (a) AGENTS.md exists somewhere in the bake; (b) every CLAUDE.md is a one-line `@AGENTS.md` redirect resolving to a sibling AGENTS.md (CLAUDE.md is optional — absence is silently fine); (c) Python-bearing templates (those declaring a project-root `pyproject.toml`) ship a `tests/` directory whose `uv run pytest` produces non-zero passing tests (slow). A fifth template added under `cookbook/` is picked up automatically at collection time and lands red on any property it doesn't satisfy.
- The eight per-template prose-checking tests landed earlier in this branch — `test_agents_md_pr_convention_is_narrative` (×3), `test_agents_md_documents_conventional_commits` (×2), `test_agents_md_documents_release_sequence`, `test_agents_md_documents_cog_block_etiquette`, `test_agents_md_documents_punch_knobs` — have been removed in favor of the discovery sweep. Substring assertions on AGENTS.md prose were too fragile and constricted prose evolution as the cookbook grows. The AGENTS.md content stays in every bake; only the tests pinning specific phrasing are gone. Subsumed parity duplicates (`test_agents_md_exists`, `test_claude_md_delegates_to_agents`, `test_does_not_ship_claude_md`, `test_baked_tests_pass`) were stripped at the same time.
- `make test` now runs `pytest -m "not slow"` and skips eight integration-heavy tests (the discovery sweep's baked-pytest rows for `python-project` / `repo-cli` / `narrative-game`, the `artifact-bench` npm-ci row, and `narrative-game`'s tweego-download / dist / rodney-Chrome integration rows). New `make test-slow` runs only the slow marker for release-prep integration completeness; `make dist` now depends on both. CI continues to invoke `make test` (now fast-only, ~9s vs. the previous ~19s). The marker discipline was already in place via `pyproject.toml`'s `[tool.pytest.ini_options].markers`; this change just flips `make test` to use it.
- Release process: tags are now mandated to be **annotated** (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`) per `docs/RELEASE.md`. Lightweight tags strand the tagger identity, timestamp, and message that `git describe`, `git log --decorate`, and the GitHub release UI all read; the published `v1.1.0` is the existing cautionary example, and the immutability rule on the git server makes a stranded lightweight tag unrecoverable except by issuing a new patch version.
- Release checklist extracted from `AGENTS.md` § Distribution into a dedicated `docs/RELEASE.md`. `AGENTS.md` § Distribution becomes a one-line pointer; the heading is preserved so existing anchor links resolve. The new file adds three pre-flight checks (uv resolution-window pin, local-and-remote tag-status sync, lockfile currency via `uv lock --check`) and an explicit post-bump `uv.lock` diff verification that the `chore(release)` commit's lockfile differs from its parent only in the `recipes` self-version line. Failure-mode workflows for both `uv lock --check` failures and post-bump-diff drift are codified, gated by the full `make test test-slow` suite — `chore(deps)` and `chore(release)` commits stay separate, with no transitive drift permitted to ride into a release commit. The two cautionary tales (`v1.1.0` lightweight + lockfile drift, `v1.1.1` release riding a `feat(template)` commit) are now documented as named tales.
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
