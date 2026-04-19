# hello-artifact

A button-counter that increments on click and persists its count via
`window.storage` when available. Demonstrates the full layered
verification loop on a near-trivial artifact:

- `@ts-check` + JSDoc on the inline `<script>` — caught by `make verify-types`
- Standards-compliant HTML — caught by `make verify-html`
- Vitest + jsdom unit test (`tests/unit.spec.ts`) — `make test-unit`

Browser-level e2e tests are deferred to a future release (see the
root README's "CI" section).

## Status

Stable. Acts as the template's smoke-test artifact; do not delete
without first replacing the unit test with an equivalent pointed at
your own artifact.
