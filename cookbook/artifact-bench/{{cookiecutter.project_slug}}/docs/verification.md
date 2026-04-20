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

## `make test` — runtime, jsdom

| Sub-target | Tool | What it catches |
|------------|------|-----------------|
| `test-unit` | `vitest` + `jsdom` | Logic exercised through the shared `load-artifact` harness — game state machines, form validation, score submission |

Browser-level e2e (real-browser interaction against `public/`) is
deferred to a future release via a lightweight rodney-based
replacement for Playwright. Until then, drive `make test-unit`'s
jsdom harness as far as it will go; assertions against the
accessible-DOM shape cover most regressions that don't depend on
real browser rendering.

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
- Persistence reset between sessions → `unit.spec.ts` against the
  storage mock.

`verify-structure` is the only enforced floor: an artifact without
README + PROMPTS won't land.
