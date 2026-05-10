# {{ cookiecutter.title }}

A Twine narrative game by {{ cookiecutter.author_name }}, scaffolded
from the `narrative-game` cookiecutter (cookbook entry in
[Gretyl/recipes](https://github.com/Gretyl/recipes)).

Story format: **{{ cookiecutter._format_proper[cookiecutter.story_format] }}**.

## Quick start

```bash
make setup-twine    # downloads tweego into .tweego/ (one-time)
make dist           # compiles src/*.twee → dist/index.html
make verify         # rodney browser smoke against the built HTML
```

Open `dist/index.html` in a browser to play.

## Layout

```
src/                # Twee 3 source — what tweego compiles
  StoryData.twee    # IFID + story-format declaration (don't delete)
  StoryTitle.twee   # the title shown in the menu
  StoryStylesheet.twee  # `[stylesheet]`-tagged passage; CSS for the page
  StoryScript.twee  # `[script]`-tagged passage; custom JS author hooks
  StoryInit.twee    # initial state (`<<set $tick to 0>>` etc.)
  Start.twee        # the entry passage; this is where play begins
examples/           # crib-sheets (NOT compiled into dist by default)
  dark-room.twee        # found-UI clicker; resource pools + log
  paperclips.twee       # numerical clicker; cooldowns + prestige
  choice-fiction.twee   # pure choice prose; branching links
scripts/install-tweego.sh   # platform-aware tweego downloader
tests/test_smoke.py         # rodney browser smoke (drives dist/index.html)
```

## Authoring

Edit any `.twee` under `src/` and re-run `make dist`. tweego concatenates
every `.twee` in the directory, so split passages across files freely.

To pull in a recipe from `examples/` (e.g. the dark-room resource-log
loop), copy or move passages from the example file into `src/` — anything
in `examples/` is reference material, not part of the build.

## Build tool

`tweego` is the canonical Twine 3 CLI compiler. The `make setup-twine`
target downloads release `2.1.1` from
[the GitHub mirror](https://github.com/tmedwards/tweego/releases) into
`.tweego/`. Override the version with `TWEEGO_VERSION=x.y.z make setup-twine`.

The bundled story formats include the four official Twine 2 formats
(SugarCube, Harlowe, Chapbook, Snowman); switch by editing the `format`
key in `src/StoryData.twee`.
