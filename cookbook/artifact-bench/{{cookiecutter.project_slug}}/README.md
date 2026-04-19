# {{cookiecutter.project_name}}

A workbench for standalone HTML artifacts — the copy-pasteable
single-file kind Claude produces — typed, tested, and iterated on
without losing the property that makes them copy-pasteable.

Deployed at <https://{{cookiecutter.deploy_host}}/>.

## Layout

```
src/<artifact-slug>/
├── artifact.html       # the shipping file, copy-pasteable
├── README.md           # what it is, current status
├── PROMPTS.md          # seed prompt + iteration log
├── notes.md            # design decisions (optional)
└── tests/              # unit.spec.ts, e2e.spec.ts (optional)
```

`public/` mirrors the deploy URLs exactly: `src/foo/artifact.html`
becomes `public/foo.html`, served from
`https://{{cookiecutter.deploy_host}}/foo.html`.

## Quickstart

```bash
make install   # npm ci + playwright install
make verify    # static checks (structure, types, html)
make test      # runtime checks (unit + e2e)
make build     # src/*/artifact.html -> public/
make ci        # verify && test && build
```

Scope to one artifact: `make verify ARTIFACT=<slug>`.

## Adding an artifact

See [docs/authoring.md](docs/authoring.md). One-paragraph version:
make a directory under `src/`, drop in `artifact.html`, write a
`README.md` and `PROMPTS.md` next to it, add an entry to
`docs/manifest.yml`. `make verify-structure` rejects an artifact
that's missing the README or PROMPTS file.

## Verifying changes

See [docs/verification.md](docs/verification.md). Two layers: fast
static checks via `make verify`, runtime browser/jsdom checks via
`make test`. Add tests opt-in, the first time you catch a regression
you wish you'd caught automatically.
{% if cookiecutter.include_github_workflows == "yes" %}
## CI

The project ships with a GitHub Actions workflow at `.github/workflows/ci.yml` with two jobs:

- **`verify`** (fast, PR-time): runs `npm ci`, `make verify`, and `make test-unit`. No browser binaries — completes in under a minute. Runs on every pull request and on push to `main`.
- **`e2e`** (browser, gated): runs `make setup-ci` (`npm ci` + Playwright browser download, ~300MB) and `make test-e2e`. Runs on push to `main`, on pull requests labeled `run-e2e`, or on manual `workflow_dispatch`. Keeping e2e off the PR path by default is deliberate — label an individual PR when you need browser-level confidence.

To run both layers locally:

```bash
make setup-ci && make ci
```

```mermaid
flowchart TB
    A[PR push] --> B[verify job]
    C[push to main] --> B
    C --> D[e2e job]
    E[PR labeled run-e2e] --> D
    F[workflow_dispatch] --> D
    B --> B1[npm ci]
    B1 --> B2[make verify]
    B2 --> B3[make test-unit]
    D --> D1[make setup-ci]
    D1 --> D2[make test-e2e]
```
{% endif %}
