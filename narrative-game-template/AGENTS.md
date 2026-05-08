# AGENTS.md — `narrative-game-template`

A cookiecutter template that scaffolds **Twine narrative-game projects**
buildable into a single self-contained HTML via the `tweego` Go binary.
The template is designed for the `cookbook/` directory of
[Gretyl/recipes](https://github.com/Gretyl/recipes); this working
develops and red/green-tests the template before the cross-repo PR.

## Quick checklist for editing this working

```
make test       # pytest (pre-bake + bake-then-post-bake)
make bake       # bake → /tmp/baked-narrative-default with defaults
make verify     # showboat verify demo.md (tightens the docs feedback loop)
make clean      # wipe /tmp bakes + .pytest_cache
```

For network-dependent rounds (downloading `tweego`, compiling Twee →
HTML, rodney browser smoke):

```
TWEEGO_NETWORK_TESTS=1 make test
```

## TDD discipline

Each numbered round in `notes.md` is **two commits** — RED test alone,
then GREEN implementation. Subjects use the working name as scope:

```
test(narrative-game-template): round N red — <behaviour pinned>
feat(narrative-game-template): round N green — <same behaviour>
```

Round 9 (rodney browser smoke) is `test-after`, not red/green — it
covers an integration path requiring real Chrome and is downstream of
build success. Subject:
`test(narrative-game-template): round 9 — rodney browser smoke (test-after)`.

See the root `AGENTS.md` "Test-driven development" section for the full
protocol; the rules followed here are unmodified from that document.

## Layout

```
narrative-game-template/
├── tests/                        # PRE-bake pytest (template source)
├── template/                     # cookiecutter root
│   ├── cookiecutter.json
│   ├── hooks/
│   └── {{cookiecutter.project_slug}}/
│       ├── src/                  # Twee 3 source consumed by tweego
│       ├── examples/             # crib-sheets — NOT compiled into dist
│       ├── scripts/install-tweego.sh
│       └── tests/test_smoke.py   # baked rodney smoke
├── data/ + charts/ + gen_charts.sh   # chartroom artefacts
└── demo.md                       # showboat-verified walkthrough
```
