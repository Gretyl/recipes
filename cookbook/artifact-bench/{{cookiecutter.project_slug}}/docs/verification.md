# Verification

Two layers, both Make-driven.

## `make verify` — fast, static, no browser

| Sub-target | Tool | What it catches |
|------------|------|-----------------|
| `verify-structure` | shell loop | Missing `README.md` or `PROMPTS.md` next to any `artifact.html` |
| `verify-types`     | `tsc --noEmit --checkJs` | Type errors in inline JSDoc-annotated scripts and in `shared/`, `scripts/` |
| `verify-html`      | `html-validate` | Malformed HTML, accessibility issues, broken attributes |

Runs in seconds. Safe to bind to a save hook. Always run before
committing.

## `make test` — runtime, jsdom + browser

| Sub-target | Tool | What it catches |
|------------|------|-----------------|
| `test-unit` | `vitest` + `jsdom` | Logic exercised through the shared `load-artifact` harness — game state machines, form validation, score submission |
| `test-e2e`  | `playwright`        | Real browser interaction against `public/` — canvas rendering, click sequences, persistence |

E2E tests require a built `public/` (Playwright's `webServer`
launches `scripts/serve.ts` to host it). Run `make build` first if
you've changed `artifact.html` since the last e2e run.

## Per-artifact scoping

Either layer accepts `ARTIFACT=<slug>` to scope:

```bash
make verify ARTIFACT=hello-artifact
make test   ARTIFACT=hello-artifact
```

This is what makes the loop livable as the repo grows — under a
second per artifact during iteration, while `make ci` covers
everything before push.

## When to add tests

Don't add tests proactively. Add them the first time you catch a
regression you wish you'd caught automatically — that's also when
you'll know exactly what assertion would have caught it.

- A click handler regressed → `unit.spec.ts` exercising the handler.
- The canvas drew the wrong frame → `e2e.spec.ts` with a screenshot
  assertion.
- Persistence reset between sessions → `unit.spec.ts` against the
  storage mock.

`verify-structure` is the only enforced floor: an artifact without
README + PROMPTS won't land.
