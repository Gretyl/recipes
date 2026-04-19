# {{cookiecutter.project_name}}

<template placeholder>

## Setup

```bash
uv sync && direnv allow
```

## Development

```bash
make test
```
{% if cookiecutter.include_github_workflows == "yes" %}
## CI

Two GitHub Actions workflows ship with this project:

- `.github/workflows/ci.yml` runs the `make test` gate on every pull request and on push to `main`.
- `.github/workflows/update-readme.yml` regenerates README content via `cog -r` on push to `main`, then commits the update if anything changed.

To run the CI test gate locally:

```bash
make setup-ci && make test
```

`make setup-ci` uses `uv sync --frozen` — the CI-specific analog of `uv sync` in `Setup`, which enforces lockfile fidelity and catches drift that would otherwise surface only in CI.

```mermaid
flowchart TB
    A[push to main] --> B[update-readme.yml]
    B --> B1[cog -r README.md]
    B1 --> B2[commit if changed]
    C[PR or push to main] --> D[ci.yml]
    D --> D1[make setup-ci]
    D1 --> D2[make test]
```
{% endif %}
## Release

```bash
make dist
```
