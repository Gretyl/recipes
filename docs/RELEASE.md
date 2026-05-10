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

> **Note:** Until we're using `uv` 0.9.17+, the `exclude-newer` setting needs to be reset to T-minus 7 days ago as an absolute timestamp. Once our `uv` supports it, switch to ISO-8601 durations instead (e.g. `P7D`).

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

Once pre-flight passes, the sequence splits across a feature branch (agent prepares the release) and a post-merge handoff (human creates and pushes the annotated tag).

### Branch preparation

Done by the agent on the feature branch.

1. Edit `pyproject.toml` (bump version) and `CHANGELOG.md` (rename `[Unreleased]` → `[X.Y.Z] - YYYY-MM-DD`, open a new empty `[Unreleased]`).
2. Run `uv sync` — regenerates `uv.lock` against the new `pyproject.toml` version. **Do this before committing**, not after; `make test` triggers `uv sync` implicitly, so running it post-commit strands lockfile changes outside the release commit.
3. **Verify the post-bump `uv.lock` diff is exactly the `recipes` self-version line** (`-version = "X.Y.<old>"` / `+version = "X.Y.<new>"` inside the `[[package]] name = "recipes"` block). Mechanical revision-counter or manifest-hash rewrites are also fine. Anything else — any other `[[package]]` block touched, dependency-array changes, packages added/removed — means transitive drift was absorbed between pre-flight step 2 and now (the index served a different snapshot, a cache TTL expired, etc.). Treat as the [post-bump verification failure path](#failure-mode-post-bump-uvlock-diff-isnt-clean) below.
4. Stage `pyproject.toml`, `CHANGELOG.md`, and `uv.lock` together. Commit as `chore(release): prepare vX.Y.Z`. The commit's diff must be exactly those three files — anything else means a separate concern leaked in.
5. Run the **pre-merge gate**: `make test test-slow` (full suite) and `uv build` (catches packaging-metadata regressions). The tag-points-at-HEAD, version/tag/CHANGELOG-match, and clean-tree assertions inside `make dist` can't run yet — those are deferred to step 9, after the human creates the tag — but `uv build` covers the same packaging surface that `make dist` would. A packaging failure caught here costs a follow-up commit on the branch; one caught post-tag costs a tag deletion and re-spec.
6. Push the branch and open a release PR. Title and body follow the [PR conventions in AGENTS.md](../AGENTS.md#pull-request-conventions).

### Merge and tag

Handoff: human merges, agent posts the tag spec, human applies it.

7. Human reviews and merges the PR using a **merge-commit** — never squash-merge or rebase-merge. See [Merge strategy](#merge-strategy) below for why; the short version is that the agent's tag spec (next step) names the SHA of the original `chore(release)` commit, and only merge-commit semantics keep that SHA reachable from `main` unchanged.
8. After observing the merge, the agent posts a **tag spec** to the human in this format:

   ```
   tag name: vX.Y.Z
   SHA: <hash of the chore(release) commit, now reachable from main>
   description: Release vX.Y.Z: <≤100-char single-line summary>
   ```

   The SHA is the original `chore(release): prepare vX.Y.Z` hash from the feature branch — unchanged after merge-commit. The description maps to `git tag -a -m`; the 100-char single-line cap keeps the tag subject scannable in `git log --decorate` and avoids drift between commit body and tag annotation.
9. Human applies the spec from a checkout of the release commit:

   ```bash
   git fetch origin
   git checkout <SHA>
   git tag -a vX.Y.Z -m "<description>"
   git cat-file -t vX.Y.Z         # must print "tag", not "commit"
   make dist                       # final validation
   git push origin vX.Y.Z
   ```

   `git checkout <SHA>` is required because `make dist` asserts tag-points-at-HEAD; running it from `main` (HEAD = merge commit, not the chore(release) commit) would fail that assertion. A clean `make dist` pass emits `dist/recipes-X.Y.Z.tar.gz` and `.whl`. If `make dist` fails, see [post-tag dist failure](#failure-mode-post-tag-make-dist-fails) — the tag is not pushed until validation passes, so a local `git tag -d vX.Y.Z` is harmless recovery.

## Merge strategy

Branches carrying a `chore(release):` commit must be merged with a **merge-commit** — never squash-merge, never rebase-merge.

The structural reason: the agent's tag spec ([Order of operations step 8](#merge-and-tag)) names the SHA of the original `chore(release)` commit, and the human's tag application ([step 9](#merge-and-tag)) operates on that SHA directly. Merge-commit preserves the SHA — the chore(release) commit stays reachable from `main` unchanged. Squash-merge synthesizes a new commit and orphans the original; rebase-merge rewrites the commit, changing its hash. Either invalidates the spec the moment the merge button is pressed, and there is no clean recovery short of re-spec'ing against whatever post-merge SHA `main` actually carries.

This rule is narrow: it applies only to branches with a `chore(release)` commit. Other branches can use whatever merge mode the team prefers.

## Annotated-tag mandate

Release tags **must** be annotated — never lightweight. The `-a` flag writes a real tag object carrying tagger identity, timestamp, and message, which is what `git describe`, `git log --decorate`, and GitHub's release UI all read. A lightweight tag (`git tag vX.Y.Z`, no `-a`) looks fine locally but strands that metadata, and because the remote rejects tag delete and tag force-push (see [tag immutability](#tag-immutability-and-recovery) below), a lightweight tag that has been pushed stays lightweight forever.

Always verify with `git cat-file -t vX.Y.Z` before pushing. Annotated → `tag`. Lightweight → `commit`.

The tag spec the agent hands off in [Order of operations step 8](#merge-and-tag) is structured so that applying it always uses `git tag -a` — the `description` field maps to `-m`, not the bare `git tag` invocation that would produce a lightweight tag. Following the spec literally is the simplest way to satisfy the mandate.

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

### Failure-mode: post-tag `make dist` fails

The agent's pre-merge gate ([Order of operations step 5](#branch-preparation)) runs `make test test-slow` + `uv build`, which covers everything `make dist` checks *except* the four assertions that need the tag itself: clean tree, version/tag/CHANGELOG match, tag exists, tag points at HEAD. So a post-tag `make dist` failure narrows to one of:

1. **Spec drift** — the tag name in the spec doesn't match the `pyproject.toml` version or the `CHANGELOG.md` section that landed on `main`. The spec was wrong; surface to the agent for a corrected re-spec, and the agent should investigate why the on-branch values diverged from what was specified.
2. **Wrong checkout** — `make dist` was run from `main` (HEAD = merge commit) instead of from the chore(release) commit. Run `git checkout <SHA>` from the spec and retry; nothing structural is wrong with the release.
3. **Dirty tree** — the human's checkout has uncommitted local changes from other work. Stash and retry; nothing structural is wrong with the release.

```
make dist fails (post-tag, pre-push)
   │
   ▼
Read the assertion the Makefile printed
   │
   ├─ "HEAD has commits since tag"
   │   → wrong checkout (case 2)
   │   → git checkout <SHA from spec>
   │   → re-run make dist
   │
   ├─ "Working tree is not clean"
   │   → dirty tree (case 3)
   │   → git stash (or commit elsewhere)
   │   → re-run make dist
   │
   └─ "Version mismatch" / "Tag <X> does not exist" / "No versioned entry in CHANGELOG"
       → spec drift (case 1)
       → git tag -d vX.Y.Z                     # delete local tag (NOT YET pushed)
       → surface the error to the agent with both:
           - the assertion text the Makefile printed
           - the on-branch pyproject/CHANGELOG values
       → wait for a corrected tag spec
       → restart from Order of operations step 9
```

The push step is the *last* action in the sequence, so a local-only tag is harmless to delete. **Do not push, then delete** — published tags are immutable on the remote (see [Tag immutability and recovery](#tag-immutability-and-recovery)). If a bad tag escapes to `origin`, the only recovery is a new patch version.

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

The order-of-operations rules this commit violated were step 2 (`uv sync` before commit) and the [Annotated-tag mandate](#annotated-tag-mandate). In the current agent/human handoff flow, both failures would now be caught earlier: `uv lock --check` (pre-flight step 2) plus the post-bump diff verification (step 3) gate the lockfile, and the tag spec format (step 8) plus `git cat-file -t` (step 9) gate the annotated-tag rule before the push.

### `v1.1.1` — release riding a feature commit

`3783920` is a `feat(template): CI workflows across cookbook templates (#30)` commit that quietly co-bundled the version bump (`1.0.0` → `1.1.1`), `uv.lock` regen, and CHANGELOG sections for both `[1.1.0]` and `[1.1.1]` inside a feature commit. The release was internally consistent (pyproject ↔ uv.lock ↔ CHANGELOG all at `1.1.1`) and the tag was correctly annotated, but the discipline was wrong: a release bundled with feature work hides exactly the kind of co-edit conflict (lockfile-vs-pyproject mismatch) that `chore(release):` exists to make visible.

The order-of-operations step 4 mandate ("the commit's diff must be exactly those three files") is the rule this commit violated.

## Tag immutability and recovery

Published tags are immutable on the git server (tag delete and tag force-push are both rejected). If a release commit lands with drift, the recovery path is a new patch version — not a retagged `X.Y.Z`. The recovery commit's body should name which earlier tag the patch is recovering.

The agent/human handoff in [Order of operations](#merge-and-tag) puts the final validation (`make dist`) between local `git tag -a` (step 9) and `git push origin vX.Y.Z` (step 9, last command), so the failure window where `git tag -d` is still safe is exactly that gap. Once `git push origin vX.Y.Z` succeeds, immutability bites and the only recovery is a new patch version.
