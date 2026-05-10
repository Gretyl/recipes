# Release Checklist

Cutting a release is a sequence that has to stay atomic: the commit tagged `vX.Y.Z` must contain a `pyproject.toml` version of `X.Y.Z`, a `CHANGELOG.md` whose top dated section is `[X.Y.Z]`, **and** a `uv.lock` regenerated against that `pyproject.toml`. If any of these drift, `make dist` fails — or, worse, ships a tag whose `uv sync --frozen` doesn't reproduce.

## Pre-flight checks

Run these in order *before* touching `pyproject.toml`'s version field. Each one guards a failure mode that has actually bitten this repo.

### 0. uv resolution-window pin

Confirm `pyproject.toml` carries:

```toml
[tool.uv]
exclude-newer = "<RFC 3339 timestamp>"
```

The cutoff should be at least seven days old. The setting shrinks uv's resolution window so packages published in the last week — yanks, supply-chain rushes, accidental publishes — are excluded from new resolutions. If absent, add it as a separate `chore(deps):` commit (see [failure-mode workflow](#failure-mode-uv-lock-check-fails) below) before proceeding to step 1; treat any post-add lockfile churn as transitive drift to absorb on its own.

### 1. Tag-status sync (local + remote)

```bash
git fetch --tags origin
git ls-remote --tags origin
git tag --list --sort=-v:refname | head
git cat-file -t v<latest-released>   # must print "tag" (annotated)
```

**Treat origin as source of truth.** The local tag database can be stale on shallow clones, restored filesystems, tags created on a different machine, or any clone that pre-dates a tag push. Verifying remote tag presence guards the failure mode where reasoning about "is this version already released?" gets answered against an empty local view — the corrective force-push path is irreversible if you're wrong.

`git cat-file -t` distinguishes annotated tags (prints `tag`) from lightweight ones (prints `commit`). `v1.1.0` is the project's existing lightweight cautionary tale; future releases must be annotated.

### 2. Lockfile currency

```bash
uv lock --check
```

Confirms the lockfile is already consistent with the *current* `pyproject.toml` (before you bump). If it fails, see [failure-mode workflow](#failure-mode-uv-lock-check-fails) below — the resolution: land a `chore(deps):` commit ahead of the release sequence, gated by the full test suite, never bundled into the chore(release) commit.

## Order of operations

Once pre-flight passes:

1. Edit `pyproject.toml` (bump version) and `CHANGELOG.md` (rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, open a new empty `[Unreleased]`).
2. Run `uv sync` — regenerates `uv.lock` against the new `pyproject.toml` version. **Do this before committing**, not after; `make test` triggers `uv sync` implicitly, so running it post-commit strands lockfile changes outside the release commit.
3. **Verify the post-bump `uv.lock` diff is exactly the `recipes` self-version line** (`-version = "X.Y.<old>"` / `+version = "X.Y.<new>"` inside the `[[package]] name = "recipes"` block). Mechanical revision-counter or manifest-hash rewrites are also fine. Anything else — any other `[[package]]` block touched, dependency-array changes, packages added/removed — means transitive drift was absorbed between pre-flight step 2 and now (the index served a different snapshot, a cache TTL expired, etc.). Treat as the [post-bump verification failure path](#failure-mode-post-bump-uvlock-diff-isnt-clean) below.
4. Stage `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` together. Commit as `chore(release): prepare vX.Y.Z`. The commit's diff must be exactly those three files — anything else means a separate concern leaked in.
5. Tag the commit with an **annotated** tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`. Verify with `git cat-file -t vX.Y.Z`: it must print `tag`, not `commit`. If it prints `commit`, delete locally (`git tag -d vX.Y.Z`) and redo with `-a`.
6. Run `make dist`. It depends on both `make test` (fast) and `make test-slow` (integration), so the full suite runs before validation; it then verifies the tag points at HEAD, the version/tag/CHANGELOG match, and the tree is clean. A clean pass emits `dist/recipes-X.Y.Z.tar.gz` and `.whl`.
7. Push branch **and** tag: `git push origin <branch> && git push origin vX.Y.Z`.

## Annotated-tag mandate

Release tags **must** be annotated — never lightweight. The `-a` flag writes a real tag object carrying tagger identity, timestamp, and message, which is what `git describe`, `git log --decorate`, and GitHub's release UI all read. A lightweight tag (`git tag vX.Y.Z`, no `-a`) looks fine locally but strands that metadata, and because the remote rejects tag delete and tag force-push (see [tag immutability](#tag-immutability-and-recovery) below), a lightweight tag that has been pushed stays lightweight forever.

Always verify with `git cat-file -t vX.Y.Z` before pushing. Annotated → `tag`. Lightweight → `commit`.

## Failure-mode workflows

### Failure-mode: `uv lock --check` fails

Three scenarios:

1. **Direct edit drift** — `pyproject.toml` was modified (dep added/removed/bumped) but `uv sync` wasn't run.
2. **Transitive drift** — a transitive released a new compatible version since last sync, and uv would now resolve differently. `pyproject.toml` itself is unchanged.
3. **Index/network failure** — environmental; fix and retry.

```
uv lock --check fails
   │
   ▼
Inspect:  uv lock --dry-run    (preview the proposed diff)
   │
   ├─ harmless / intentional ─►  uv sync
   │                             git add uv.lock
   │                             git commit -m "chore(deps): refresh lockfile to current resolutions"
   │                             uv lock --check                # must now pass
   │                             make test test-slow            # FULL SUITE — gate the drift
   │                                  ├─ green ─►  resume release sequence
   │                                  └─ red ───►  diagnose; pin/revert; loop
   │
   └─ surprising / suspect ───►  uv tree / changelogs / advisories
                                 pin or constrain in pyproject if needed
                                 git commit -m "chore(deps): constrain <pkg> to <version>"
                                 retry uv lock --check
                                 make test test-slow            # FULL SUITE, same as above
```

### Failure-mode: post-bump `uv.lock` diff isn't clean

Pre-flight `uv lock --check` proved the lockfile was clean *before* the bump, but the post-bump `uv sync` (order-of-operations step 2) re-resolves against the index, which can serve different snapshots than the pre-flight saw — across cache TTLs, multi-machine workflows, or other timing gaps.

```
git diff -- uv.lock
   │
   ├─ exactly one hunk: recipes self-version (mechanical revision/hash also OK)
   │   → proceed to chore(release) commit
   │
   └─ any other [[package]] block touched / dependency array changed /
      package added or removed
      → git checkout -- uv.lock pyproject.toml CHANGELOG.md   # roll back the in-progress bump
      → uv sync                                                # absorb the drift alone
      → git diff uv.lock | review                              # decide intentional vs. suspect
      → git add uv.lock
        git commit -m "chore(deps): refresh lockfile to current resolutions"
      → make test test-slow                                    # FULL SUITE — gate the drift
      → only on green: re-run order-of-operations from step 1
      → re-verify the step-2 diff is now one-line clean
```

### Why the full suite (not just `make test`)

Lockfile drift can move transitive dependencies enough to silently shift runtime behavior. The fast `make test` gate misses the integration-heavy `@pytest.mark.slow` rows: baked-pytest across `python-project` / `repo-cli` / `narrative-game`, the `artifact-bench` `npm ci` row, and `narrative-game`'s tweego-download / dist / rodney-Chrome integration rows. A dependency change is exactly the class of risk where `test-slow` matters — exotic interactions with subprocess Python toolchains, baked-template `uv sync --frozen` sensitivity, and headless-browser surfaces show up there and nowhere else. **`chore(deps):` and `chore(release):` get the same gate**: the full suite passes before either commit lands as a release prerequisite.

## Cautionary tales

### `v1.1.0` — stranded lightweight tag with lockfile drift

`b2c1c9a` is a `chore(release): prepare v1.1.0` commit where:
- `pyproject.toml` was bumped to `1.1.0`,
- `uv sync` was **skipped**,
- so `uv.lock` still pinned `recipes` at `1.0.0`,
- and the resulting drift commit was tagged **lightweight** (no `-a`).

`uv sync --frozen` against the published tag fails. The lightweight tag can't be deleted from the remote (immutability rule), so the recovery was a new patch — `v1.1.1`.

### `v1.1.1` — release riding a feature commit

`3783920` is a `feat(template): CI workflows across cookbook templates (#30)` commit that quietly co-bundled the version bump (`1.0.0` → `1.1.1`), `uv.lock` regen, and CHANGELOG sections for both `[1.1.0]` and `[1.1.1]` inside a feature commit. The release was internally consistent (pyproject ↔ uv.lock ↔ CHANGELOG all at `1.1.1`) and the tag was correctly annotated, but the discipline was wrong: a release bundled with feature work hides exactly the kind of co-edit conflict (lockfile-vs-pyproject mismatch) that `chore(release):` exists to make visible.

The order-of-operations step 4 mandate ("the commit's diff must be exactly those three files") is the rule this commit violated.

## Tag immutability and recovery

Published tags are immutable on the git server (tag delete and tag force-push are both rejected). If a release commit lands with drift, the recovery path is a new patch version — not a retagged `X.Y.Z`. The recovery commit's body should name which earlier tag the patch is recovering.
