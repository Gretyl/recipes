# {{cookiecutter.project_slug}}/Makefile
.PHONY: help install verify verify-structure verify-types verify-html \
        test test-unit test-e2e build ci clean
.DEFAULT_GOAL := help

# Discover artifacts (supports src/foo/ and src/category/foo/)
ARTIFACT_DIRS := $(dir $(wildcard src/*/artifact.html src/*/*/artifact.html))

# Scope to one artifact: `make test ARTIFACT=implode`
ARTIFACT ?=
SCOPE    := $(if $(ARTIFACT),src/$(ARTIFACT),src)

help:
	@echo "Targets:"
	@echo "  install      npm deps + playwright browsers"
	@echo "  verify       static checks   (structure, types, html)"
	@echo "  test         runtime checks  (unit + e2e)"
	@echo "  build        src/*/artifact.html -> public/"
	@echo "  ci           verify && test && build"
	@echo "  clean        remove generated output"
	@echo ""
	@echo "Scope to one: make <target> ARTIFACT=implode"

install:
	npm ci
	npx playwright install --with-deps

# ---- verify: fast, static, no browser, no jsdom ----

verify: verify-structure verify-types verify-html

verify-structure:
	@echo "-> every artifact has README.md + PROMPTS.md"
	@for d in $(ARTIFACT_DIRS); do \
	  test -f $$d/README.md  || { echo "MISSING $$d/README.md";  exit 1; }; \
	  test -f $$d/PROMPTS.md || { echo "MISSING $$d/PROMPTS.md"; exit 1; }; \
	done
	@echo "ok structure"

verify-types:
	@echo "-> tsc --checkJs on inline scripts (via JSDoc @ts-check)"
	npx tsc --noEmit -p tsconfig.json

verify-html:
	@echo "-> html-validate"
	npx html-validate "$(SCOPE)/**/artifact.html"

# ---- test: runtime ----

test: test-unit test-e2e

test-unit:
	@echo "-> vitest (jsdom/happy-dom)"
	npx vitest run $(SCOPE)

test-e2e:
	@echo "-> playwright"
	npx playwright test $(if $(ARTIFACT),--grep "$(ARTIFACT)",)

# ---- build + meta ----

build:
	npx tsx scripts/build.ts
	npx tsx scripts/gallery.ts

ci: verify test build

clean:
	rm -rf public/ test-results/ playwright-report/ node_modules/.vitest
