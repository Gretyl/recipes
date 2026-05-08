.DEFAULT_GOAL := help

# Toolchain detection — system tweego first, then a project-local one
# under .tweego/ (populated by `make setup-twine`). The
# AGENTS.md "Non-Python toolchains" pattern: detect via `command -v`,
# fall back to a `setup-<lang>` target when absent.
TWEEGO := $(shell command -v tweego 2>/dev/null)
LOCAL_TWEEGO := $(CURDIR)/.tweego/tweego
ifeq ($(TWEEGO),)
TWEEGO := $(shell test -x $(LOCAL_TWEEGO) && echo $(LOCAL_TWEEGO))
endif

SRC := $(wildcard src/*.twee)

help:
	@printf "%-14s %s\n" "Target" "Description"
	@printf "%-14s %s\n" "------" "-----------"
	@printf "%-14s %s\n" "setup-twine"  "Download tweego into .tweego/ for this project."
	@printf "%-14s %s\n" "dist"         "Compile src/*.twee → dist/index.html via tweego."
	@printf "%-14s %s\n" "test"         "Pre-commit gate: setup-twine + dist + rodney browser smoke."
	@printf "%-14s %s\n" "clean"        "Remove dist/ and .tweego/."

setup-twine:
	@./scripts/install-tweego.sh

dist: dist/index.html

dist/index.html: $(SRC)
ifdef TWEEGO
	@mkdir -p dist
	@echo "📦 Compiling src/ → $@ via $(TWEEGO)"
	@$(TWEEGO) -o $@ src/
else
	@echo "⚠️  Skipping dist (tweego not found — run 'make setup-twine' first)"
endif

# `test` is the single pre-commit gate per Gretyl/recipes cookbook
# convention: it chains setup-twine → dist → the rodney browser smoke
# under pytest. Sub-make calls (rather than prerequisites) so each
# phase re-parses the Makefile and picks up the .tweego/tweego
# binary that setup-twine just installed — TWEEGO := $(shell …) is
# evaluated at parse time, so within a single make invocation the
# detection cannot see binaries that didn't exist when make started.
test:
	@$(MAKE) setup-twine
	@$(MAKE) dist
	@uv run --extra test --extra dev pytest -v tests/

clean:
	@rm -rf dist/ .tweego/

.PHONY: help setup-twine dist test clean
