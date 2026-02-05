.DEFAULT_GOAL := help

help:
	@printf "%-12s %s\n" "Target" "Description"
	@printf "%-12s %s\n" "------" "-----------"
	@printf "%-12s %s\n" "check" "Lint and auto-fix issues with ruff."
	@printf "%-12s %s\n" "clean" "Remove build, cache, venv, and lock artifacts."
	@printf "%-12s %s\n" "format" "Format code using ruff."
	@printf "%-12s %s\n" "mypy" "Type-check sources with mypy after format/check."
	@printf "%-12s %s\n" "repo_map" "Regenerate docs/repo_map.md from project sources."
	@printf "%-12s %s\n" "test" "Run tests with coverage after check and format."

# Define the directories to be cleaned or mapped
PYTHON_DIRS = {{cookiecutter.package_name}}/ tests/

# Clean up .pyc files by finding and deleting them in specified directories
clean:
	@echo "🧼 Cleaning build, test, and cache artifacts..."
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

repo_map: clean docs/repo_map.md
	@echo "🗺️  Regenerating repo map..."
	@files-to-prompt -m -o docs/repo_map.md $(PYTHON_DIRS)
	@echo "`cat docs/repo_map.md | wc -l` lines => `ttok -i docs/repo_map.md` tokens"

test: check format
	@echo "🧪 Running tests with coverage..."
	@pytest --doctest-modules --cov={{cookiecutter.package_name}} -v

check:
	@echo "🐶 Checking code with ruff (fixing issues)..."
	@ruff check --fix

format:
	@echo "✍️  Formatting code with ruff..."
	@ruff format

mypy: format check
	@echo "🥧  Running mypy..."
	@mypy $(PYTHON_DIRS)

.PHONY: help clean test check format mypy repo_map
