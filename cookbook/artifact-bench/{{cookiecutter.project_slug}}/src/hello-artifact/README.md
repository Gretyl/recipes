# hello-artifact

A button-counter that increments on click and persists its count via
`window.storage` when available. Demonstrates the full layered
verification loop on a near-trivial artifact:

- `@ts-check` + JSDoc on the inline `<script>` — caught by `make verify-types`
- Standards-compliant HTML — caught by `make verify-html`
- Vitest + jsdom unit test (`tests/unit.spec.ts`) — `make test-unit`
- Playwright e2e against the built `public/hello-artifact.html` — `make test-e2e`

## Status

Stable. Acts as the template's smoke-test artifact; do not delete
without first replacing the unit/e2e tests with equivalents pointed at
your own artifact.
