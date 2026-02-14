# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-02-13

### Added

- Templated `make dist` target for `python-project` cookbook.  #10
- `generalize` and `meld makefiles` CLI subcommands.  #9
- Bake-level tests for `python-project` template.  #9

### Fixed

- Template Makefile and mypy issues in `python-project`; v1.0 quality pass.  #9

### Changed

- Migrated project instructions to `AGENTS.md`.
- Removed `scripts/*.py` from `python-project` template output.

## [0.9.0] - 2026-02-13

### Added

- Template extension: `template.py` with `apply` and `prepare` subcommands for Cog-based README management.
- GitHub Actions workflow option (`include_github_workflow`) with `update-readme.yml`.
- Post-generation hook to conditionally remove `.github/` directory.
- 54 template-level tests in baked output (test_template, test_template_apply, test_template_prepare).
- First bake-level test suite (`tests/test_bake_repo_cli.py`).

## [0.1.0] - 2026-02-04

### Added

- Initial release of Recipes CLI.
