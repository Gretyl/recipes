# artifact-bench template demo

*2026-04-19T16:02:29Z by Showboat 0.6.1*
<!-- showboat-id: 1f2f5655-6207-49d3-b12e-4ac0eb2c2a18 -->

The artifact-bench template scaffolds a Node/TypeScript workbench for standalone HTML artifacts — the copy-pasteable single-file kind Claude produces — typed, tested, and iterated on without losing the property that makes them copy-pasteable. v1.1 ships four layered verifications (structure, tsc --checkJs, html-validate, vitest/jsdom unit tests) all wired through a single CI workflow. Browser-level e2e is deferred to v1.2 via a rodney-based replacement.

Bake with defaults (project_name=Fresh Artifacts, include_example_artifact=no, include_github_workflows=yes):

```bash
rm -rf /tmp/ab-demo-default && /home/user/recipes/.venv/bin/cookiecutter /home/user/recipes/cookbook/artifact-bench --no-input --output-dir /tmp/ab-demo-default && find /tmp/ab-demo-default/fresh-artifacts -type f | sort | sed "s|/tmp/ab-demo-default/||"
```

```output
fresh-artifacts/.gitattributes
fresh-artifacts/.github/workflows/ci.yml
fresh-artifacts/.gitignore
fresh-artifacts/.htmlvalidate.json
fresh-artifacts/AGENTS.md
fresh-artifacts/CHANGELOG.md
fresh-artifacts/CLAUDE.md
fresh-artifacts/Makefile
fresh-artifacts/README.md
fresh-artifacts/docs/authoring.md
fresh-artifacts/docs/manifest.yml
fresh-artifacts/docs/verification.md
fresh-artifacts/package-lock.json
fresh-artifacts/package.json
fresh-artifacts/public/.gitkeep
fresh-artifacts/scripts/build.ts
fresh-artifacts/scripts/check-all.ts
fresh-artifacts/scripts/gallery.ts
fresh-artifacts/shared/harness/load-artifact.ts
fresh-artifacts/shared/harness/storage-mock.ts
fresh-artifacts/shared/types/claude-storage.d.ts
fresh-artifacts/src/.gitkeep
fresh-artifacts/tsconfig.json
fresh-artifacts/vitest.config.ts
```

Default bake omits the example artifact (src/ has just .gitkeep) so the workbench is ready to accept the author's first artifact. Setting include_example_artifact=yes ships a hello-artifact demo that exercises the full verification harness:

```bash
rm -rf /tmp/ab-demo-example && /home/user/recipes/.venv/bin/cookiecutter /home/user/recipes/cookbook/artifact-bench --no-input --output-dir /tmp/ab-demo-example include_example_artifact=yes && find /tmp/ab-demo-example/fresh-artifacts/src -type f | sort | sed "s|/tmp/ab-demo-example/||"
```

```output
fresh-artifacts/src/hello-artifact/PROMPTS.md
fresh-artifacts/src/hello-artifact/README.md
fresh-artifacts/src/hello-artifact/artifact.html
fresh-artifacts/src/hello-artifact/notes.md
fresh-artifacts/src/hello-artifact/tests/unit.spec.ts
```

The Makefile drives the four-layer verification plus build:

```bash
make -C /tmp/ab-demo-example/fresh-artifacts help
```

```output
make: Entering directory '/tmp/ab-demo-example/fresh-artifacts'
Targets:
  install      npm dependencies
  verify       static checks   (structure, types, html)
  test         runtime checks  (unit)
  build        src/*/artifact.html -> public/
  ci           verify && test && build
  clean        remove generated output

Scope to one: make <target> ARTIFACT=implode
make: Leaving directory '/tmp/ab-demo-example/fresh-artifacts'
```

The CI workflow runs a single verify job on every pull request and on push to main. No browser binaries — the gate completes in under a minute:

```bash
cat /tmp/ab-demo-example/fresh-artifacts/.github/workflows/ci.yml
```

```output
# CI workflow for fresh-artifacts.
#
# Runs the fast verify gate on every pull request and on push to main:
# npm ci + make verify + make test-unit. No browser binaries — the
# job completes in under a minute.
#
# End-to-end (browser) tests are deferred to a future release via a
# lightweight rodney-based replacement.

name: CI

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install npm dependencies
        run: npm ci

      - name: Run static checks
        run: make verify

      - name: Run unit tests
        run: make test-unit
```

Baking with include_github_workflows=no removes the `.github/` directory via the post-generation hook:

```bash
rm -rf /tmp/ab-demo-no-wf && /home/user/recipes/.venv/bin/cookiecutter /home/user/recipes/cookbook/artifact-bench --no-input --output-dir /tmp/ab-demo-no-wf include_github_workflows=no 2>&1; test -d /tmp/ab-demo-no-wf/fresh-artifacts/.github && echo ".github/ exists" || echo "No .github/ directory"; test -f /tmp/ab-demo-no-wf/fresh-artifacts/Makefile && echo "Makefile present"; grep -c "## CI" /tmp/ab-demo-no-wf/fresh-artifacts/README.md || echo "README has no ## CI section"
```

```output
No .github/ directory
Makefile present
0
README has no ## CI section
```

The deploy_host cookiecutter variable threads through the README and `docs/manifest.yml`, so the baked project is ready to point at its own public URL:

```bash
grep -n "deploy_host\|gretyl.maplecrew.org" /tmp/ab-demo-default/fresh-artifacts/README.md /tmp/ab-demo-default/fresh-artifacts/docs/manifest.yml | head -5
```

```output
/tmp/ab-demo-default/fresh-artifacts/README.md:7:Deployed at <https://gretyl.maplecrew.org/>.
/tmp/ab-demo-default/fresh-artifacts/README.md:22:`https://gretyl.maplecrew.org/foo.html`.
/tmp/ab-demo-default/fresh-artifacts/README.md:53:`https://gretyl.maplecrew.org/<slug>.html`.
/tmp/ab-demo-default/fresh-artifacts/docs/manifest.yml:4:# https://gretyl.maplecrew.org/<route>.
```

Setting the optional `primary_artifact_slug` swaps the generic workbench lead for an INSTANCE-flavored opener that names the canonical artifact and threads the slug through the deploy URL. Title derives from the slug via Jinja's built-in `replace`+`title` filter chain, so one variable is enough for a single-canonical-artifact instance:

```bash
rm -rf /tmp/ab-demo-instance && /home/user/recipes/.venv/bin/cookiecutter /home/user/recipes/cookbook/artifact-bench --no-input --output-dir /tmp/ab-demo-instance primary_artifact_slug=artemis-trail && sed -n "1,7p" /tmp/ab-demo-instance/fresh-artifacts/README.md
```

```output
# Fresh Artifacts

Hosting **Artemis Trail** as the canonical artifact of this `artifact-bench` instance.

Play: <https://gretyl.maplecrew.org/artemis-trail.html>
Gallery: <https://gretyl.maplecrew.org/>

```
