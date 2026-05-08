include $(shell git rev-parse --show-toplevel)/trace.mk

.DEFAULT_GOAL := help

BAKE_DIR := /tmp/baked-narrative-default

help:
	@printf "%-12s %s\n" "Target" "Description"
	@printf "%-12s %s\n" "------" "-----------"
	@printf "%-12s %s\n" "test"   "pytest pre-bake + bake-then-post-bake suite."
	@printf "%-12s %s\n" "bake"   "Bake template into $(BAKE_DIR) with defaults."
	@printf "%-12s %s\n" "verify" "Run pytest + showboat verify demo.md."
	@printf "%-12s %s\n" "clean"  "Remove $(BAKE_DIR) and pytest caches."

test:
	@uv run --extra test pytest

bake:
	@rm -rf $(BAKE_DIR)
	@uv run --extra test python -c \
		"from cookiecutter.main import cookiecutter; \
		 cookiecutter('template', no_input=True, output_dir='/tmp', \
		              extra_context={'project_slug': 'baked-narrative-default'})"

verify: test
	@./gen_charts.sh
	@echo "✓ pytest passed; charts regenerated. demo.md is hand-authored reference,"
	@echo "  not a showboat-captured session — its screenshots are reproducible by"
	@echo "  the rodney sequences documented in §'Build & verify' of demo.md."

clean:
	@rm -rf $(BAKE_DIR) .pytest_cache __pycache__ tests/__pycache__

.PHONY: help test bake verify clean
