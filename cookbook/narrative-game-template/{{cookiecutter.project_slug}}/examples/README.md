# Authoring crib-sheets

Three `.twee` files demonstrating SugarCube macros for the three
opinionated forms this template ships against. None of them are
compiled into `dist/index.html` by default — tweego is only pointed
at `src/`. To use a recipe, copy the passages you want from one of
these files into a new `.twee` under `src/`, drop the per-file prefix
(`DR_`, `PC_`, `CF_`), and re-run `make dist`.

| File | Form | Reference titles |
|---|---|---|
| [`dark-room.twee`](dark-room.twee) | found-UI clicker — resource pools + log + gradual unlocks | *A Dark Room* (Doublespeak Games) |
| [`paperclips.twee`](paperclips.twee) | numerical clicker — cooldowns, multipliers, prestige | *Universal Paperclips* (Frank Lantz) |
| [`choice-fiction.twee`](choice-fiction.twee) | pure choice-based branching prose | recent IFComp / Spring Thing winners |

Each file uses **SugarCube** macros (`<<button>>`, `<<set>>`,
`<<replace>>`, `<<if>>`, `<<print>>`, `[[link]]`). For Harlowe,
Chapbook, or Snowman, the same primitives exist but with different
syntax — see each format's documentation.
