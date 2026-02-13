.DEFAULT_GOAL := help

help:
	@printf "%-12s %s\n" "Target" "Description"
	@printf "%-12s %s\n" "------" "-----------"
	@printf "%-12s %s\n" "check" "Lint and auto-fix issues with ruff."
	@printf "%-12s %s\n" "clean" "Remove build, cache, venv, and lock artifacts."
	@printf "%-12s %s\n" "format" "Format code using ruff."
	@printf "%-12s %s\n" "mypy" "Type-check sources with mypy after format/check."
	@printf "%-12s %s\n" "test" "Run tests with coverage after check and format."

# Define the directories to be checked and tested
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

test: check format
	@echo "🧪 Running tests with coverage..."
	@pytest --doctest-modules --cov={{cookiecutter.package_name}} -v $(PYTHON_DIRS)

check:
	@echo "🐶 Checking code with ruff (fixing issues)..."
	@ruff check --fix

format:
	@echo "✍️  Formatting code with ruff..."
	@ruff format

mypy: format check
	@echo "🥧  Running mypy..."
	@mypy $(PYTHON_DIRS)

.PHONY: help clean test check format mypy
