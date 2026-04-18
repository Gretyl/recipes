# Prompts — hello-artifact

A running log of the prompts that produced this artifact, in order.
Append new prompts at the bottom; never edit history. The point is
provenance: another author should be able to read this file and
understand how the artifact got to its current shape.

---

## 1. Initial generation

> Build me a tiny single-file HTML artifact: a button labeled "Click me"
> next to a counter that increments on each click. Persist the count
> across reloads. Use `@ts-check` and JSDoc on the inline `<script>`.
> Keep it under 50 lines.

## 2. Storage hardening

> The counter should still work in environments where `window.storage`
> is not defined (regular browsers, jsdom without our shim). Make the
> persistence calls optional-chained so it degrades to in-memory only.
