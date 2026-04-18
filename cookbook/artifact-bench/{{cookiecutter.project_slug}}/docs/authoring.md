# Authoring an artifact

## What an artifact is

A standalone HTML file that runs as-is in a browser tab — single
file, inline `<script>`, optional CDN imports. Each artifact lives in
its own directory under `src/` and ships with a small set of
siblings:

```
src/<artifact-slug>/
├── artifact.html       # the shipping file, copy-pasteable into Claude
├── README.md           # one-paragraph description and current status
├── PROMPTS.md          # seed prompt + iteration log
├── notes.md            # design decisions (optional)
├── fixtures/           # seeded data, save states (optional)
└── tests/              # unit.spec.ts, e2e.spec.ts (optional, layered)
```

`artifact.html` is the **only required file** alongside `README.md`
and `PROMPTS.md`. Everything else is opt-in and gets added the first
time you wish a regression had been caught automatically.

## Adding one

1. `mkdir src/<slug> && cd src/<slug>`
2. Drop your `artifact.html` in.
3. Write a one-paragraph `README.md` and seed `PROMPTS.md` with the
   prompt that produced the file.
4. `make verify` — the structure check rejects missing README/PROMPTS.
5. Add an entry to `docs/manifest.yml` so the gallery picks it up.

## Typing inline scripts

Use TypeScript via JSDoc on the inline `<script>` block:

```html
<script>
// @ts-check
/** @param {number} n */
function double(n) { return n * 2; }
</script>
```

`make verify-types` runs `tsc --checkJs` over every artifact under
`src/`. Catches the obvious bugs without a build step.

## Persistent state

Artifacts that need persistence call `window.storage` (the Claude
artifact storage API). It's `undefined` outside Claude, so handle the
absent case explicitly:

```js
const store = window.storage;
if (store) store.setItem("score", String(score));
```

The unit-test harness (`shared/harness/load-artifact.ts`) injects an
in-memory mock of `window.storage` so persistence-related logic
stays testable.
