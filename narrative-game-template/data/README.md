# Chart data

CSVs feeding `gen_charts.sh`. Edit these and re-run the script to
regenerate the PNGs in `../charts/`.

## `story_format_features.csv`

`feature_score` is a count of supported features for each format,
out of 7:

| Feature | SugarCube | Harlowe | Chapbook | Snowman |
|---|---|---|---|---|
| Resource macros (`<<set>>`, counters) | ✓ | ✓ | ✓ | — |
| Save/load (built-in) | ✓ | ✓ | ✓ | — |
| JS escape hatch (custom JS in passages) | ✓ | partial | ✓ | ✓ |
| Custom CSS via stylesheet passage | ✓ | ✓ | ✓ | ✓ |
| Timed events / auto-tick | ✓ | ✓ | partial | — |
| Repeat blocks / loops | ✓ | ✓ | — | — |
| Found-UI ergonomics (`<<button>>`-heavy) | ✓ | partial | partial | — |

Justifies SugarCube as the cookiecutter default.

## `form_primitive_usage.csv`

`primitives_used` is a count of mechanical primitives each form
leans on, out of 8 (resource pool, action button, cooldown, event
interrupt, upgrade, passage transition, log append, prestige/restart).

A choice-fiction story typically uses only passage transition (and
sometimes a small resource pool); a paperclips-style clicker uses
all eight. Visualises why one Twine project can express all three
forms — the primitives overlap, and SugarCube has the macros for
all of them.
