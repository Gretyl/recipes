.DEFAULT_GOAL := help

help:
	@printf "%-12s %s\n" "Target" "Description"
	@printf "%-12s %s\n" "------" "-----------"
	@printf "%-12s %s\n" "check" "Lint and auto-fix issues with ruff."
	@printf "%-12s %s\n" "clean" "Remove build, cache, venv, lock, and dist artifacts."
	@printf "%-12s %s\n" "dist" "Prepare a versioned release in dist/."
	@printf "%-12s %s\n" "format" "Format code using ruff."
	@printf "%-12s %s\n" "mypy" "Type-check sources with mypy after format/check."
	@printf "%-12s %s\n" "setup-ci" "Install CI-locked dependencies (uv sync --frozen)."
	@printf "%-12s %s\n" "test" "Run fast tests with coverage after check, format, and mypy."
	@printf "%-12s %s\n" "test-slow" "Run slow integration tests (release-prep gate; runs as a dependency of dist)."

# Define the directories to be checked and tested
PYTHON_DIRS = recipes/ recipes_cli/ tests/

# Clean up build, cache, venv, lock, and dist artifacts
clean:
	@echo "🧼 Cleaning build, test, cache, and dist artifacts..."
	@rm -rf \
		__pycache__/ \
		**/__pycache__/ \
		*.pyc \
		*.pyo \
		*.pyd \
		build/ \
		dist/ \
		*.egg-info/ \
		.coverage \
		.mypy_cache/ \
		.pytest_cache/ \
		.ruff_cache/ \
		uv.lock \
		.venv/

test: check format mypy
	@echo "🧪 Running fast tests with coverage..."
	@uv run pytest -m "not slow" --doctest-modules --cov=recipes --cov=recipes_cli -v $(PYTHON_DIRS)

test-slow:
	@echo "🐢 Running slow integration tests..."
	@uv run pytest -m "slow" -v $(PYTHON_DIRS)

check:
	@echo "🐶 Checking code with ruff (fixing issues)..."
	@uv run ruff check --fix

format:
	@echo "✍️  Formatting code with ruff..."
	@uv run ruff format

mypy: format check
	@echo "🥧  Running mypy..."
	@uv run mypy $(PYTHON_DIRS)

setup-ci:
	@echo "📦 Installing CI-locked dependencies..."
	@uv sync --frozen

dist: test test-slow
	@echo "📦 Preparing versioned release..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "❌ Error: Working tree is not clean."; \
		echo "   Commit or stash all changes before building a release."; \
		echo ""; \
		echo "   Unresolved changes:"; \
		git status --short; \
		exit 1; \
	fi
	@PKG_VERSION=$$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1); \
	CL_VERSION=$$(sed -n 's/^## \[\([0-9][^ ]*\)\].*/\1/p' CHANGELOG.md | head -1); \
	if [ -z "$$PKG_VERSION" ]; then \
		echo "❌ Error: Could not read version from pyproject.toml."; \
		exit 1; \
	fi; \
	if [ -z "$$CL_VERSION" ]; then \
		echo "❌ Error: No versioned entry found in CHANGELOG.md."; \
		echo "   Add an entry like: ## [0.1.0] - YYYY-MM-DD"; \
		exit 1; \
	fi; \
	if [ "$$PKG_VERSION" != "$$CL_VERSION" ]; then \
		echo "❌ Error: Version mismatch."; \
		echo "   pyproject.toml version: $$PKG_VERSION"; \
		echo "   CHANGELOG.md version:   $$CL_VERSION"; \
		echo "   Update CHANGELOG.md or pyproject.toml so both versions match."; \
		exit 1; \
	fi; \
	TAG="v$$PKG_VERSION"; \
	TAG_COMMIT=$$(git rev-list -n1 "$$TAG" 2>/dev/null); \
	if [ -z "$$TAG_COMMIT" ]; then \
		echo "❌ Error: Tag $$TAG does not exist."; \
		echo "   Create the release tag: git tag $$TAG"; \
		exit 1; \
	fi; \
	HEAD_COMMIT=$$(git rev-parse HEAD); \
	if [ "$$TAG_COMMIT" != "$$HEAD_COMMIT" ]; then \
		echo "❌ Error: HEAD has commits since tag $$TAG."; \
		echo "   Tag $$TAG points to: $$(git rev-parse --short $$TAG_COMMIT)"; \
		echo "   HEAD is at:          $$(git rev-parse --short HEAD)"; \
		echo "   Ensure the release tag is on the current commit."; \
		exit 1; \
	fi; \
	echo "✅ All release checks passed for version $$PKG_VERSION."; \
	uv build --out-dir dist/

.PHONY: help clean test test-slow check format mypy setup-ci dist
