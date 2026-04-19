"""Bake-level tests for the artifact-bench cookiecutter template.

These tests programmatically run cookiecutter against the template
with default and custom contexts, then verify the resulting file
trees and file contents.
"""

import json
import pathlib
import shutil
import subprocess

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_DIRECTORY = str(
    pathlib.Path(__file__).parent.parent / "cookbook" / "artifact-bench"
)


class TestBakeDefaults:
    """Bake with default context values from cookiecutter.json."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        tmp_path = tmp_path_factory.mktemp("defaults")
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
        )
        return tmp_path / "fresh-artifacts"

    def test_output_directory_exists(self, baked: pathlib.Path) -> None:
        assert baked.is_dir()

    def test_makefile_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "Makefile").is_file()

    def test_package_json_exists(self, baked: pathlib.Path) -> None:
        assert (baked / "package.json").is_file()

    def test_makefile_defines_layered_targets(self, baked: pathlib.Path) -> None:
        """The Makefile is the developer interface — verify/test/build/ci/clean must be wired."""
        makefile = (baked / "Makefile").read_text()
        # Join line-continuations so multi-line .PHONY declarations parse as one.
        joined = makefile.replace("\\\n", " ")
        phony_line = next(
            line for line in joined.splitlines() if line.startswith(".PHONY:")
        )
        phony_targets = set(phony_line.removeprefix(".PHONY:").split())
        for target in ("verify", "test", "build", "ci", "clean"):
            assert f"{target}:" in makefile, f"missing target: {target}"
            assert target in phony_targets, f"target {target} not declared .PHONY"

    def test_makefile_verify_splits_structure_types_html(
        self, baked: pathlib.Path
    ) -> None:
        """verify is the static-checks gate — it must compose the three sub-targets."""
        makefile = (baked / "Makefile").read_text()
        verify_line = next(
            line
            for line in makefile.splitlines()
            if line.startswith(("verify:", "verify "))
        )
        assert "verify-structure" in verify_line
        assert "verify-types" in verify_line
        assert "verify-html" in verify_line

    def test_makefile_supports_artifact_scoping(self, baked: pathlib.Path) -> None:
        """ARTIFACT= is the per-artifact scoping knob the proposal calls out."""
        makefile = (baked / "Makefile").read_text()
        assert "ARTIFACT" in makefile
        assert "ARTIFACT ?=" in makefile

    def test_package_json_declares_required_devdeps(self, baked: pathlib.Path) -> None:
        """The Makefile invokes npx tsc/html-validate/vitest/playwright/tsx — package.json must provide them."""
        pkg = json.loads((baked / "package.json").read_text())
        dev_deps = pkg.get("devDependencies", {})
        for required in (
            "typescript",
            "html-validate",
            "@playwright/test",
            "vitest",
            "jsdom",
            "tsx",
            "js-yaml",
        ):
            assert required in dev_deps, f"missing devDependency: {required}"

    def test_package_json_omits_scripts_block(self, baked: pathlib.Path) -> None:
        """Make is the interface — package.json scripts would compete and confuse."""
        pkg = json.loads((baked / "package.json").read_text())
        assert "scripts" not in pkg, (
            "package.json must not duplicate Makefile interface"
        )

    def test_tsconfig_enables_checkjs_dom_strict(self, baked: pathlib.Path) -> None:
        """The proposal's authoring story rests on tsc --checkJs over inline JSDoc; DOM lib is required for window/document."""
        ts = json.loads((baked / "tsconfig.json").read_text())
        opts = ts.get("compilerOptions", {})
        assert opts.get("checkJs") is True
        assert opts.get("allowJs") is True
        assert opts.get("strict") is True
        assert opts.get("noEmit") is True
        lib = opts.get("lib", [])
        assert any(item == "DOM" or item.lower() == "dom" for item in lib)

    def test_tsconfig_includes_src_shared_scripts(self, baked: pathlib.Path) -> None:
        """The three first-class source roots must be in tsconfig.include."""
        ts = json.loads((baked / "tsconfig.json").read_text())
        include = set(ts.get("include", []))
        assert "src/**/*" in include
        assert "shared/**/*" in include
        assert "scripts/**/*" in include

    def test_html_validate_config_extends_recommended(
        self, baked: pathlib.Path
    ) -> None:
        """html-validate is the static-HTML gate — it must extend the recommended preset."""
        cfg = json.loads((baked / ".html-validate.json").read_text())
        extends = cfg.get("extends", [])
        assert any("html-validate:recommended" in item for item in extends)

    def test_playwright_config_targets_e2e_specs(self, baked: pathlib.Path) -> None:
        """playwright.config.ts must restrict testMatch to e2e.spec.ts so unit specs don't double-run."""
        cfg = (baked / "playwright.config.ts").read_text()
        assert "e2e.spec.ts" in cfg
        assert "testDir" in cfg

    def test_vitest_config_targets_unit_specs_with_jsdom(
        self, baked: pathlib.Path
    ) -> None:
        """vitest.config.ts must scope to unit.spec.ts and use the jsdom environment."""
        cfg = (baked / "vitest.config.ts").read_text()
        assert "unit.spec.ts" in cfg
        assert "jsdom" in cfg

    def test_claude_storage_shim_declares_window_storage(
        self, baked: pathlib.Path
    ) -> None:
        """Claude artifacts use window.storage; without a shim, every typed artifact errors on first reference."""
        shim_path = baked / "shared" / "types" / "claude-storage.d.ts"
        assert shim_path.is_file()
        shim = shim_path.read_text()
        assert "window" in shim.lower() or "Window" in shim
        assert "storage" in shim.lower()

    def test_scripts_implement_build_gallery_check_serve(
        self, baked: pathlib.Path
    ) -> None:
        """The Makefile invokes tsx scripts/{build,gallery}.ts; playwright invokes scripts/serve.ts; check-all is the orchestrator referenced in the proposal."""
        scripts = baked / "scripts"
        for name in ("build.ts", "gallery.ts", "check-all.ts", "serve.ts"):
            assert (scripts / name).is_file(), f"missing scripts/{name}"
        build_src = (scripts / "build.ts").read_text()
        # build walks src/ and writes to public/
        assert "src" in build_src
        assert "public" in build_src
        gallery_src = (scripts / "gallery.ts").read_text()
        assert "manifest.yml" in gallery_src
        assert "public" in gallery_src

    def test_load_artifact_harness_uses_jsdom_and_storage_mock(
        self, baked: pathlib.Path
    ) -> None:
        """unit specs need a single entry point that mounts an artifact in jsdom with storage mocked."""
        loader = baked / "shared" / "harness" / "load-artifact.ts"
        mock = baked / "shared" / "harness" / "storage-mock.ts"
        assert loader.is_file()
        assert mock.is_file()
        loader_src = loader.read_text()
        assert "jsdom" in loader_src
        assert "JSDOM" in loader_src
        # Loader must wire the storage mock into the jsdom window.
        assert "storage" in loader_src.lower()
        mock_src = mock.read_text()
        assert "getItem" in mock_src
        assert "setItem" in mock_src

    def test_docs_authoring_and_verification_exist(self, baked: pathlib.Path) -> None:
        """docs/authoring.md and docs/verification.md back the README's links and onboard new users."""
        assert (baked / "docs" / "authoring.md").is_file()
        assert (baked / "docs" / "verification.md").is_file()

    def test_manifest_yml_references_deploy_host(self, baked: pathlib.Path) -> None:
        """gallery.ts reads docs/manifest.yml; the example route must use deploy_host so users see how to fill it in."""
        manifest = (baked / "docs" / "manifest.yml").read_text()
        assert "gretyl.maplecrew.org" in manifest
        # And it must declare the artifacts: top-level key gallery.ts expects.
        assert "artifacts:" in manifest

    def test_readme_starts_with_project_name_and_references_deploy_host(
        self, baked: pathlib.Path
    ) -> None:
        """The README is the first thing a cloner reads — it must name the project and point at the deploy URL."""
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# Fresh Artifacts")
        assert "gretyl.maplecrew.org" in readme

    def test_readme_links_to_authoring_and_verification_docs(
        self, baked: pathlib.Path
    ) -> None:
        """README must hand off to docs/ for deeper how-tos so it doesn't reproduce them inline."""
        readme = (baked / "README.md").read_text()
        assert "docs/authoring.md" in readme
        assert "docs/verification.md" in readme

    def test_gitignore_excludes_node_modules_and_build_output(
        self, baked: pathlib.Path
    ) -> None:
        """A fresh clone must not commit node_modules, public/ build output, or test reports."""
        gitignore = (baked / ".gitignore").read_text()
        for pattern in (
            "node_modules",
            "public/",
            "test-results",
            "playwright-report",
        ):
            assert pattern in gitignore, f".gitignore missing pattern: {pattern}"

    def test_gitattributes_marks_binary_extensions(self, baked: pathlib.Path) -> None:
        """recipes generalize-style tools detect binaries via .gitattributes; without entries, binary assets get mangled."""
        attrs = (baked / ".gitattributes").read_text()
        for ext in ("png", "jpg"):
            assert ext in attrs, f".gitattributes missing extension: {ext}"

    def test_default_bake_omits_example_artifact(self, baked: pathlib.Path) -> None:
        """Default include_example_artifact=no — the hello-artifact tree must not survive the post-gen hook."""
        assert not (baked / "src" / "hello-artifact").exists()

    def test_default_bake_seeds_src_gitkeep(self, baked: pathlib.Path) -> None:
        """An empty src/ would not be tracked by git; .gitkeep preserves the layout for the first artifact."""
        assert (baked / "src" / ".gitkeep").is_file()

    def test_default_bake_seeds_public_gitkeep(self, baked: pathlib.Path) -> None:
        """public/ is gitignored except for .gitkeep — preserves the deploy-target directory."""
        assert (baked / "public" / ".gitkeep").is_file()

    def test_default_bake_ships_changelog_with_unreleased_section(
        self, baked: pathlib.Path
    ) -> None:
        """A web-artifact workbench iterates on designs over time; CHANGELOG.md is where each deploy/iteration gets recorded."""
        changelog = baked / "CHANGELOG.md"
        assert changelog.is_file()
        text = changelog.read_text()
        assert "Keep a Changelog" in text
        assert "[Unreleased]" in text


class TestBakeWithExample:
    """Bake with include_example_artifact=yes — the worked example must survive."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        tmp_path = tmp_path_factory.mktemp("with-example")
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={"include_example_artifact": "yes"},
        )
        return tmp_path / "fresh-artifacts"

    def test_example_artifact_html_uses_ts_check(self, baked: pathlib.Path) -> None:
        """The example demonstrates the JSDoc-typed inline-script pattern — @ts-check is the gateway."""
        artifact = baked / "src" / "hello-artifact" / "artifact.html"
        assert artifact.is_file()
        content = artifact.read_text()
        assert "@ts-check" in content

    def test_example_bake_omits_src_gitkeep(self, baked: pathlib.Path) -> None:
        """When the example tree ships, src/ is no longer empty — .gitkeep would be redundant noise."""
        assert not (baked / "src" / ".gitkeep").exists()

    def test_example_e2e_spec_loads_from_public(self, baked: pathlib.Path) -> None:
        """tests/e2e.spec.ts must hit the built artifact under public/ — that's what playwright.config.ts serves and what production deploys."""
        spec = baked / "src" / "hello-artifact" / "tests" / "e2e.spec.ts"
        assert spec.is_file()
        text = spec.read_text()
        assert "@playwright/test" in text
        assert "hello-artifact" in text
        # It should reference a route, not a file path — playwright serves public/ over HTTP.
        assert "/hello-artifact" in text or "hello-artifact.html" in text

    def test_example_unit_spec_uses_shared_harness(self, baked: pathlib.Path) -> None:
        """tests/unit.spec.ts must import the shared loader so future artifacts copy the pattern instead of reinventing jsdom setup."""
        spec = baked / "src" / "hello-artifact" / "tests" / "unit.spec.ts"
        assert spec.is_file()
        text = spec.read_text()
        assert "load-artifact" in text, "unit spec must import the shared harness"
        assert "vitest" in text, "unit spec must use vitest"

    def test_example_sibling_docs_demonstrate_artifact_layout(
        self, baked: pathlib.Path
    ) -> None:
        """An artifact directory pairs artifact.html with PROMPTS.md (history), README.md (status), notes.md (decisions)."""
        art_dir = baked / "src" / "hello-artifact"
        prompts = art_dir / "PROMPTS.md"
        readme = art_dir / "README.md"
        notes = art_dir / "notes.md"
        assert prompts.is_file()
        assert readme.is_file()
        assert notes.is_file()
        # PROMPTS.md should look like a prompt log, not an empty placeholder.
        prompts_text = prompts.read_text()
        assert "prompt" in prompts_text.lower()
        # README should name the artifact so a reader knows what it is.
        assert (
            "hello-artifact" in readme.read_text().lower()
            or "hello artifact" in readme.read_text().lower()
        )


class TestBakeCustomContext:
    """Bake with custom values for every variable — defaults must not leak into the output."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        tmp_path = tmp_path_factory.mktemp("custom")
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={
                "project_name": "Cosmic Demos",
                "project_slug": "cosmic-demos",
                "deploy_host": "demo.example.com",
                "include_example_artifact": "yes",
            },
        )
        return tmp_path / "cosmic-demos"

    def test_custom_project_slug_names_output_directory(
        self, baked: pathlib.Path
    ) -> None:
        """The output directory takes its name from project_slug — without this, every bake collides at fresh-artifacts/."""
        assert baked.is_dir()
        assert baked.name == "cosmic-demos"

    def test_custom_project_slug_propagates_to_package_json_name(
        self, baked: pathlib.Path
    ) -> None:
        """package.json's name must reflect project_slug so npm and downstream tooling identify the project correctly."""
        pkg = json.loads((baked / "package.json").read_text())
        assert pkg["name"] == "cosmic-demos"

    def test_custom_deploy_host_appears_in_readme(self, baked: pathlib.Path) -> None:
        """The README's gallery section advertises the live URL — without substitution, every fork shows the template author's host."""
        readme = (baked / "README.md").read_text()
        assert "demo.example.com" in readme

    def test_custom_deploy_host_appears_in_manifest(self, baked: pathlib.Path) -> None:
        """docs/manifest.yml drives the gallery; if deploy_host doesn't propagate, the gallery links to the wrong domain."""
        manifest = (baked / "docs" / "manifest.yml").read_text()
        assert "demo.example.com" in manifest

    def test_custom_project_name_titles_readme(self, baked: pathlib.Path) -> None:
        """The README opens with the project name — without it, every fork's first line says 'Fresh Artifacts'."""
        readme = (baked / "README.md").read_text()
        assert readme.startswith("# Cosmic Demos")

    def test_no_default_values_leak_into_text_files(self, baked: pathlib.Path) -> None:
        """Sweep every text file for the three default values — any hit means a hardcoded substring escaped Jinja substitution."""
        defaults = ("fresh-artifacts", "Fresh Artifacts", "gretyl.maplecrew.org")
        text_suffixes = {
            ".md",
            ".json",
            ".yml",
            ".yaml",
            ".html",
            ".ts",
            ".js",
            ".tsx",
            ".jsx",
            ".css",
            ".txt",
            ".d.ts",
            ".gitignore",
            ".gitattributes",
        }
        leaks: list[tuple[pathlib.Path, str]] = []
        for path in baked.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in text_suffixes and path.name not in {
                "Makefile",
                ".gitignore",
                ".gitattributes",
                ".html-validate.json",
            }:
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            for default in defaults:
                if default in text:
                    leaks.append((path.relative_to(baked), default))
        assert not leaks, f"default values leaked into custom-context bake: {leaks}"

    def test_no_unrendered_cookiecutter_tokens(self, baked: pathlib.Path) -> None:
        """An unrendered `{{ cookiecutter.* }}` is a Jinja substitution that the engine missed — usually a typo or escape gone wrong."""
        offenders: list[pathlib.Path] = []
        for path in baked.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if "cookiecutter." in text and "{{" in text:
                offenders.append(path.relative_to(baked))
        assert not offenders, f"unrendered cookiecutter tokens remain: {offenders}"


class TestBakeWithWorkflow:
    """Tests specific to include_github_workflows='yes' in artifact-bench."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        tmp_path = tmp_path_factory.mktemp("workflow")
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={"include_github_workflows": "yes"},
        )
        return tmp_path / "fresh-artifacts"

    # ---- ci.yml shape ----

    def test_ci_workflow_file_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".github" / "workflows" / "ci.yml").is_file()

    def test_ci_workflow_defines_verify_job(self, baked: pathlib.Path) -> None:
        """The fast PR-time job must be named verify so readers map it to make verify."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "verify:" in yml

    def test_ci_workflow_defines_e2e_job(self, baked: pathlib.Path) -> None:
        """The gated browser job must be named e2e so readers map it to make test-e2e."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "e2e:" in yml

    def test_ci_workflow_triggers_include_pull_request(
        self, baked: pathlib.Path
    ) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "pull_request:" in yml

    def test_ci_workflow_triggers_include_push_to_main(
        self, baked: pathlib.Path
    ) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "push:" in yml
        assert "main" in yml

    def test_ci_workflow_triggers_include_workflow_dispatch(
        self, baked: pathlib.Path
    ) -> None:
        """workflow_dispatch is the escape hatch for running e2e against any branch."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "workflow_dispatch:" in yml

    def test_ci_workflow_filters_on_run_e2e_label(self, baked: pathlib.Path) -> None:
        """Propagation: the label name must match what reviewers add to PRs."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "run-e2e" in yml

    def test_ci_verify_job_invokes_npm_ci(self, baked: pathlib.Path) -> None:
        """Verify job does npm ci directly (skipping playwright install) to stay fast."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "npm ci" in yml

    def test_ci_verify_job_invokes_make_verify(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make verify" in yml

    def test_ci_verify_job_invokes_make_test_unit(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make test-unit" in yml

    def test_ci_e2e_job_invokes_make_setup_ci(self, baked: pathlib.Path) -> None:
        """Propagation: e2e routes the heavy install through make setup-ci."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make setup-ci" in yml

    def test_ci_e2e_job_invokes_make_test_e2e(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make test-e2e" in yml

    # ---- Makefile ----

    def test_makefile_defines_setup_ci_target(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        assert "setup-ci:" in makefile

    def test_makefile_setup_ci_runs_npm_ci_and_playwright(
        self, baked: pathlib.Path
    ) -> None:
        """setup-ci installs npm deps + playwright browsers for the e2e job."""
        makefile = (baked / "Makefile").read_text()
        lines = makefile.splitlines()
        setup_ci_idx = next(
            i for i, line in enumerate(lines) if line.startswith("setup-ci:")
        )
        recipe = []
        for line in lines[setup_ci_idx + 1 :]:
            if line and not line.startswith(("\t", " ")):
                break
            recipe.append(line)
        recipe_text = "\n".join(recipe)
        assert "npm ci" in recipe_text
        assert "playwright install" in recipe_text

    def test_makefile_setup_ci_is_phony(self, baked: pathlib.Path) -> None:
        makefile = (baked / "Makefile").read_text()
        joined = makefile.replace("\\\n", " ")
        phony_line = next(
            line for line in joined.splitlines() if line.startswith(".PHONY:")
        )
        assert "setup-ci" in phony_line

    def test_makefile_help_lists_setup_ci(self, baked: pathlib.Path) -> None:
        """Propagation: make help must advertise the new target."""
        makefile = (baked / "Makefile").read_text()
        help_idx = next(
            i
            for i, line in enumerate(makefile.splitlines())
            if line.startswith("help:")
        )
        help_block = "\n".join(makefile.splitlines()[help_idx : help_idx + 30])
        assert "setup-ci" in help_block

    def test_makefile_install_target_untouched(self, baked: pathlib.Path) -> None:
        """install is the local-dev affordance; setup-ci is the CI equivalent. Both exist side by side."""
        makefile = (baked / "Makefile").read_text()
        assert "install:" in makefile

    # ---- README CI section ----

    def test_readme_has_ci_section(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "## CI" in readme

    def test_readme_ci_section_names_workflow_file(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert ".github/workflows/ci.yml" in readme

    def test_readme_ci_section_names_both_jobs(self, baked: pathlib.Path) -> None:
        """Propagation: renames to the ci.yml job names must update the README.
        Scoped to the ## CI section so incidental uses of 'verify' / 'e2e'
        elsewhere don't hide a regression in the CI docs themselves."""
        readme = (baked / "README.md").read_text()
        ci_start = readme.find("## CI")
        assert ci_start != -1, "README has no ## CI section"
        ci_end = readme.find("\n## ", ci_start + len("## CI"))
        if ci_end == -1:
            ci_end = len(readme)
        ci_section = readme[ci_start:ci_end].lower()
        assert "verify" in ci_section
        assert "e2e" in ci_section

    def test_readme_ci_section_documents_run_e2e_label(
        self, baked: pathlib.Path
    ) -> None:
        """Propagation: a reviewer must be able to find the exact label name from the README."""
        readme = (baked / "README.md").read_text()
        assert "run-e2e" in readme

    def test_readme_ci_section_documents_workflow_dispatch(
        self, baked: pathlib.Path
    ) -> None:
        readme = (baked / "README.md").read_text()
        assert "workflow_dispatch" in readme

    def test_readme_ci_section_has_mermaid_flowchart(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "```mermaid" in readme
        assert "flowchart" in readme

    def test_readme_mermaid_names_all_make_targets(self, baked: pathlib.Path) -> None:
        """Propagation: the flowchart must name every make target the workflow invokes.
        If ci.yml adds or renames a target, the flowchart must track it."""
        readme = (baked / "README.md").read_text()
        start = readme.find("```mermaid")
        end = readme.find("```", start + len("```mermaid"))
        mermaid = readme[start:end]
        assert "make setup-ci" in mermaid
        assert "make verify" in mermaid
        assert "make test-unit" in mermaid
        assert "make test-e2e" in mermaid


class TestBakeWithoutWorkflow:
    """Tests specific to include_github_workflows='no' in artifact-bench."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        tmp_path = tmp_path_factory.mktemp("no-workflow")
        cookiecutter(
            template=TEMPLATE_DIRECTORY,
            output_dir=str(tmp_path),
            no_input=True,
            extra_context={"include_github_workflows": "no"},
        )
        return tmp_path / "fresh-artifacts"

    def test_no_github_directory(self, baked: pathlib.Path) -> None:
        assert not (baked / ".github").exists()

    def test_readme_has_no_ci_section(self, baked: pathlib.Path) -> None:
        """When the flag is no, the CI section must not leak into the README."""
        readme = (baked / "README.md").read_text()
        assert "## CI" not in readme

    def test_install_target_still_present(self, baked: pathlib.Path) -> None:
        """Inverse sanity: the hook only removes .github/; the local-dev install stays."""
        makefile = (baked / "Makefile").read_text()
        assert "install:" in makefile


# ---------------------------------------------------------------------------
# End-to-end smoke: bake, install, run `make ci` inside the output.
# Gated by @pytest.mark.slow so it only runs when explicitly enabled.
# Guards the combined correctness of Makefile targets, package.json
# devDeps, and the new CI workflow shape — any regression in those
# surfaces here as a red slow test.
# ---------------------------------------------------------------------------


@pytest.mark.slow()
@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed")
def test_baked_artifact_bench_verify_job_runs_green(
    tmp_path: pathlib.Path,
) -> None:
    """Smoke test: replays the fast ci.yml verify job locally.

    A fresh bake with the example artifact must pass
    ``npm install`` + ``make verify`` + ``make test-unit``. This
    matches what ci.yml's verify job runs on every PR — if it
    greens here, the PR-time gate will green in CI.

    The smoke test covers the static layers (structure, types,
    html-validate) and the jsdom unit spec. The e2e layer
    (Playwright) is not part of the smoke: running playwright
    locally needs browser infrastructure that varies across dev
    environments, and e2e regressions are caught by ci.yml's gated
    e2e job against real GitHub runners. This matches the fast/
    gated split the workflow already expresses.
    """
    cookiecutter(
        template=TEMPLATE_DIRECTORY,
        output_dir=str(tmp_path),
        no_input=True,
        extra_context={"include_example_artifact": "yes"},
    )
    baked = tmp_path / "fresh-artifacts"

    install = subprocess.run(
        ["npm", "install"],
        cwd=baked,
        capture_output=True,
        text=True,
        check=False,
    )
    assert install.returncode == 0, (
        f"npm install failed:\n{install.stdout}\n{install.stderr}"
    )

    verify = subprocess.run(
        ["make", "verify"],
        cwd=baked,
        capture_output=True,
        text=True,
        check=False,
    )
    assert verify.returncode == 0, (
        f"make verify failed:\n{verify.stdout}\n{verify.stderr}"
    )

    test_unit = subprocess.run(
        ["make", "test-unit"],
        cwd=baked,
        capture_output=True,
        text=True,
        check=False,
    )
    assert test_unit.returncode == 0, (
        f"make test-unit failed:\n{test_unit.stdout}\n{test_unit.stderr}"
    )
