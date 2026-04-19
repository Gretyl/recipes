# artifact-bench template notes

## Approach

This is the first **non-Python** template in the cookbook. It scaffolds a
Node/TypeScript workbench for managing standalone HTML artifacts — the
single-file copy-pasteable HTML that Claude emits — with a layered
verification harness on top. Source of truth for the design is the
[artifact-bench proposal](https://gist.githubusercontent.com/Gretyl/29472dc6d9cd88f754cad0def3f3a976/raw/da31f7a7d4c2d5775f539654d5c4e99ec251f9a7/artifact-bench-proposal.md).

The four pillars carried over from the proposal:

1. One artifact = one directory with `artifact.html` untouched.
2. Layered, opt-in verification: structure → types → html → unit → e2e.
3. First-class prompt history in `PROMPTS.md`.
4. `public/` mirrors deploy URLs exactly so the e2e suite is just a
   browser hitting the same paths production serves.

## Key cookiecutter variables

- **`project_name`** — display name; titles the README. Defaults to
  `Fresh Artifacts`.
- **`project_slug`** — output directory and `package.json` name.
  Defaults to `fresh-artifacts`.
- **`deploy_host`** — bare hostname (no scheme) of the deploy target.
  Used in `README.md` gallery copy and `docs/manifest.yml`. Defaults to
  `gretyl.maplecrew.org` so a one-shot `cookiecutter ...` produces a
  ready-to-publish gallery for the recipe author's own deploy. Override
  for any other host.
- **`include_example_artifact`** — yes/no list, defaulting to **`no`**.
  When `no`, the post-gen hook deletes `src/hello-artifact/` and writes
  `src/.gitkeep`. The default is empty-scaffold because the typical
  first move is "drop in my artifact and prompts" — shipping the
  example unprompted means the user spends their first 60 seconds
  deleting things. `yes` is for showcase bakes (demos,
  walkthroughs) where seeing the full layered loop on a working
  artifact matters.

## Decisions and tradeoffs

- **Make is the developer interface, not `npm scripts`.** Matches the
  rest of the cookbook ("Makefile is the interface"). `package.json`
  intentionally has no `scripts` block — duplicating the Make targets
  there would create two competing surfaces and rot independently. The
  bake test pins `"scripts" not in pkg`.
- **Inline `<script>` typing via `// @ts-check` + JSDoc**, not TS
  source files. Artifacts must remain copy-pasteable single-file HTML —
  a build step that emits `.html` from `.ts` would break the contract.
  `tsc --checkJs --noEmit` over the inline scripts gets us strict
  typing without changing the output.
- **Shared harness lives in `shared/harness/`**, not duplicated per
  artifact. `load-artifact.ts` is the single jsdom-mount entry point;
  `storage-mock.ts` is the in-memory `window.storage` shim. New
  artifact authors copy the unit-spec template and import the harness
  rather than reinventing setup.
- **`window.storage` shim is real.** Claude artifacts assume
  `window.storage` exists; without `shared/types/claude-storage.d.ts`,
  every typed artifact fails type-check on its first storage
  reference. The example artifact uses optional chaining
  (`store?.getItem`) so it degrades gracefully when the shim is
  absent (e.g., a vanilla browser opening `public/`).
- **`public/` is gitignored except for `.gitkeep`.** Build output
  doesn't belong in version control; `.gitkeep` keeps the deploy-target
  directory tracked so a fresh clone has somewhere for `make build` to
  write.

## Documentation surface outside `cookbook/`

Four files outside `cookbook/` were updated to make the new template
discoverable. They're listed here so a future template author can
follow the same checklist:

- `README.md` — Cog block lists templates by walking `cookbook/*` for
  `cookiecutter.json`. Re-running Cog after adding the directory
  generates the bullet automatically.
- `CHANGELOG.md` — `[Unreleased]` → `### Added` bullet for the new
  template.
- `AGENTS.md` (root) — the "primary template is python-project" line
  was misleading once a non-Python template existed; now enumerates
  all three templates.
- `cookbook/AGENTS.md` — the Template Conventions list (uv, hatchling,
  ruff, mypy, pytest) describes Python templates only. Added a
  one-line scope note so non-Python templates don't appear to violate
  the conventions.

## Deferred work

- **`npm install` smoke test.** The bake tests run cookiecutter and
  inspect the output tree but never install dependencies or run
  `make ci`. Pinning the actual verification chain (tsc, html-validate,
  vitest, playwright) requires Node + browser binaries on CI, which
  the recipes repo does not yet provision. Add this as a
  `@pytest.mark.slow` test once a Node-capable runner is wired up. The
  in-tree `scripts/` and configs are well-typed enough that the test
  is a thin shell wrapper.
- **`cookbook/demos/artifact-bench.md`.** Per `cookbook/AGENTS.md`,
  demos are written by `uvx showboat` once the template is ready to
  commit. Run it as the immediate follow-up to this PR — the demo
  output should walk both bake variants (with and without the
  example) and reference the same deploy host the README mentions.

## Anti-patterns avoided

- **No `package.json` scripts block.** See above; Make is the
  interface.
- **No top-level `docs/artifact-bench.md` in the recipes repo.** The
  proposal is the spec; the template embeds `docs/authoring.md` and
  `docs/verification.md` inside the baked output, where end-users
  actually need them.
- **No batched `tsconfig`/`vitest`/`playwright` scaffold commits.**
  Each config landed as its own red→green pair so the TDD log is a
  reviewable sequence of falsifiable claims about the template, not a
  giant "scaffold the configs" diff.
