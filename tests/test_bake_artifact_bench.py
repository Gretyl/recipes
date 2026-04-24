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

from tests.helpers import bake, mermaid_block, readme_section


class TestBakeDefaults:
    """Bake with default context values from cookiecutter.json."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake("artifact-bench", tmp_path_factory.mktemp("defaults"))

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
        """The Makefile invokes npx tsc/html-validate/vitest/tsx — package.json must provide them."""
        pkg = json.loads((baked / "package.json").read_text())
        dev_deps = pkg.get("devDependencies", {})
        for required in (
            "typescript",
            "html-validate",
            "vitest",
            "jsdom",
            "tsx",
            "js-yaml",
        ):
            assert required in dev_deps, f"missing devDependency: {required}"

    def test_package_json_omits_playwright(self, baked: pathlib.Path) -> None:
        """Playwright is descoped for v1.1; the browser-e2e layer returns in v1.2 via rodney."""
        pkg = json.loads((baked / "package.json").read_text())
        dev_deps = pkg.get("devDependencies", {})
        assert "@playwright/test" not in dev_deps

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
        cfg = json.loads((baked / ".htmlvalidate.json").read_text())
        extends = cfg.get("extends", [])
        assert any("html-validate:recommended" in item for item in extends)

    def test_no_playwright_config(self, baked: pathlib.Path) -> None:
        """playwright.config.ts is descoped for v1.1; rodney-based e2e in v1.2 won't reuse it."""
        assert not (baked / "playwright.config.ts").exists()

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

    def test_scripts_implement_build_gallery_check(self, baked: pathlib.Path) -> None:
        """The Makefile invokes tsx scripts/{build,gallery}.ts; check-all is the orchestrator referenced in the proposal. scripts/serve.ts is descoped alongside playwright."""
        scripts = baked / "scripts"
        for name in ("build.ts", "gallery.ts", "check-all.ts"):
            assert (scripts / name).is_file(), f"missing scripts/{name}"
        assert not (scripts / "serve.ts").exists()
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

    def test_readme_does_not_reproduce_adding_an_artifact_section(
        self, baked: pathlib.Path
    ) -> None:
        """docs/authoring.md (§ 'Adding one') is the single source of truth for the homing flow; a one-paragraph duplicate in README forces every instance to rewrite it."""
        readme = (baked / "README.md").read_text()
        assert "## Adding an artifact" not in readme, (
            "README.md must not ship a one-paragraph '## Adding an artifact' "
            "section — the flow lives in docs/authoring.md (§ 'Adding one')"
        )
        authoring = (baked / "docs" / "authoring.md").read_text()
        assert "## Adding one" in authoring, (
            "docs/authoring.md must keep its '## Adding one' section — it's "
            "the single source of truth after the README hoist"
        )

    def test_gitignore_excludes_node_modules_and_build_output(
        self, baked: pathlib.Path
    ) -> None:
        """A fresh clone must not commit node_modules or public/ build output."""
        gitignore = (baked / ".gitignore").read_text()
        for pattern in (
            "node_modules",
            "public/",
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

    def test_default_bake_keeps_generic_workbench_lead(
        self, baked: pathlib.Path
    ) -> None:
        """Inverse branch of the primary_artifact_slug conditional: when the variable is empty (the default), the generic 'A workbench for standalone HTML artifacts' lead must render and the INSTANCE-flavored 'Hosting **<title>**' opener must NOT leak through."""
        readme = (baked / "README.md").read_text()
        assert "A workbench for standalone HTML artifacts" in readme, (
            "default bake must keep the generic multi-artifact lead — "
            "without it, punches that don't name a canonical artifact "
            "have no opening framing"
        )
        assert "Hosting **" not in readme, (
            "default bake must not render the INSTANCE-flavored opener "
            "that's scoped to punches with primary_artifact_slug set"
        )


class TestBakePrimaryArtifactSlug:
    """Bake with a set primary_artifact_slug — the README opens with an INSTANCE-flavored block that names the canonical artifact and threads the slug into the deploy URL."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("instance"),
            extra_context={"primary_artifact_slug": "artemis-trail"},
        )

    @pytest.fixture(scope="class")
    def single_word_baked(
        self, tmp_path_factory: pytest.TempPathFactory
    ) -> pathlib.Path:
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("instance-sw"),
            extra_context={"primary_artifact_slug": "implode"},
        )

    def test_instance_opener_names_canonical_artifact(
        self, baked: pathlib.Path
    ) -> None:
        """Behavior: when primary_artifact_slug is set, the README opens with a 'Hosting **<title>** as the canonical artifact' line so a reader knows at a glance what the workbench hosts."""
        readme = (baked / "README.md").read_text()
        assert (
            "Hosting **Artemis Trail** as the canonical artifact of this `artifact-bench` instance."
            in readme
        )

    def test_instance_opener_propagates_slug_to_deploy_url(
        self, baked: pathlib.Path
    ) -> None:
        """Propagation: the slug must thread into the Play URL — without substitution every instance's opener would point at a placeholder path."""
        readme = (baked / "README.md").read_text()
        assert "Play: <https://gretyl.maplecrew.org/artemis-trail.html>" in readme

    def test_instance_opener_replaces_generic_workbench_lead(
        self, baked: pathlib.Path
    ) -> None:
        """The instance opener and the generic lead must not coexist — two different framings at the top of the README contradict each other."""
        readme = (baked / "README.md").read_text()
        assert "A workbench for standalone HTML artifacts" not in readme

    def test_title_derives_from_single_word_slug(
        self, single_word_baked: pathlib.Path
    ) -> None:
        """Title derivation: a single-word slug like 'implode' must render as 'Implode' — title-case of the slug, no hyphen replacement needed. Proves the Jinja filter chain handles slugs without internal hyphens cleanly."""
        readme = (single_word_baked / "README.md").read_text()
        assert "Hosting **Implode**" in readme


class TestBakeWithExample:
    """Bake with include_example_artifact=yes — the worked example must survive."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("with-example"),
            extra_context={"include_example_artifact": "yes"},
        )

    def test_example_artifact_html_uses_ts_check(self, baked: pathlib.Path) -> None:
        """The example demonstrates the JSDoc-typed inline-script pattern — @ts-check is the gateway."""
        artifact = baked / "src" / "hello-artifact" / "artifact.html"
        assert artifact.is_file()
        content = artifact.read_text()
        assert "@ts-check" in content

    def test_example_bake_omits_src_gitkeep(self, baked: pathlib.Path) -> None:
        """When the example tree ships, src/ is no longer empty — .gitkeep would be redundant noise."""
        assert not (baked / "src" / ".gitkeep").exists()

    def test_no_example_e2e_spec(self, baked: pathlib.Path) -> None:
        """tests/e2e.spec.ts is descoped alongside playwright; the v1.2 rodney-based
        replacement will land its own replacement example."""
        spec = baked / "src" / "hello-artifact" / "tests" / "e2e.spec.ts"
        assert not spec.exists()

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
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("custom"),
            extra_context={
                "project_name": "Cosmic Demos",
                "project_slug": "cosmic-demos",
                "deploy_host": "demo.example.com",
                "include_example_artifact": "yes",
            },
        )

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
                ".htmlvalidate.json",
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
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("workflow"),
            extra_context={"include_github_workflows": "yes"},
        )

    # ---- ci.yml shape ----

    def test_ci_workflow_file_exists(self, baked: pathlib.Path) -> None:
        assert (baked / ".github" / "workflows" / "ci.yml").is_file()

    def test_ci_workflow_defines_verify_job(self, baked: pathlib.Path) -> None:
        """v1.1 ships a single verify job. The e2e job returns in v1.2 via rodney."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "verify:" in yml

    def test_ci_workflow_has_no_e2e_job(self, baked: pathlib.Path) -> None:
        """Playwright is descoped for v1.1; no job line should mention e2e."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "e2e:" not in yml

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

    def test_ci_workflow_has_no_label_or_dispatch_triggers(
        self, baked: pathlib.Path
    ) -> None:
        """workflow_dispatch and the run-e2e label gated the descoped e2e job; without e2e, neither is needed."""
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "workflow_dispatch" not in yml
        assert "run-e2e" not in yml

    def test_ci_verify_job_invokes_npm_ci(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "npm ci" in yml

    def test_ci_verify_job_invokes_make_verify(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make verify" in yml

    def test_ci_verify_job_invokes_make_test_unit(self, baked: pathlib.Path) -> None:
        yml = (baked / ".github" / "workflows" / "ci.yml").read_text()
        assert "make test-unit" in yml

    # ---- Makefile ----

    def test_makefile_has_no_setup_ci_or_test_e2e_targets(
        self, baked: pathlib.Path
    ) -> None:
        """Both descoped alongside playwright for v1.1. They return in v1.2."""
        makefile = (baked / "Makefile").read_text()
        assert "setup-ci:" not in makefile
        assert "test-e2e:" not in makefile

    def test_makefile_install_target_present(self, baked: pathlib.Path) -> None:
        """install is the local-dev affordance — survives the playwright descope."""
        makefile = (baked / "Makefile").read_text()
        assert "install:" in makefile

    # ---- README CI section ----

    def test_readme_has_ci_section(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "## CI" in readme

    def test_readme_ci_section_names_workflow_file(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert ".github/workflows/ci.yml" in readme

    def test_readme_ci_section_names_verify_job(self, baked: pathlib.Path) -> None:
        """Scoped to the ## CI section so incidental 'verify' mentions elsewhere
        don't hide a regression in the CI docs themselves."""
        readme = (baked / "README.md").read_text()
        assert "verify" in readme_section(readme, "CI").lower()

    def test_readme_ci_section_flags_e2e_deferred_to_v1_2(
        self, baked: pathlib.Path
    ) -> None:
        """A puncher must see that browser-level e2e is intentional future work,
        not a forgotten gap."""
        readme = (baked / "README.md").read_text()
        assert "rodney" in readme_section(readme, "CI").lower()

    def test_readme_ci_section_has_mermaid_flowchart(self, baked: pathlib.Path) -> None:
        readme = (baked / "README.md").read_text()
        assert "```mermaid" in readme
        assert "flowchart" in readme

    def test_readme_mermaid_names_verify_make_targets(
        self, baked: pathlib.Path
    ) -> None:
        """Propagation: the flowchart must name every make target the workflow invokes.
        If ci.yml adds or renames a target, the flowchart must track it."""
        readme = (baked / "README.md").read_text()
        mermaid = mermaid_block(readme)
        assert "make verify" in mermaid
        assert "make test-unit" in mermaid
        # run-e2e / make setup-ci / make test-e2e must NOT appear — those
        # are descoped until v1.2.
        assert "make setup-ci" not in mermaid
        assert "make test-e2e" not in mermaid


class TestBakeWithoutWorkflow:
    """Tests specific to include_github_workflows='no' in artifact-bench."""

    @pytest.fixture(scope="class")
    def baked(self, tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
        return bake(
            "artifact-bench",
            tmp_path_factory.mktemp("no-workflow"),
            extra_context={"include_github_workflows": "no"},
        )

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
    """Smoke test: replays the ci.yml verify job locally.

    A fresh bake with the example artifact must pass
    ``npm install`` + ``make verify`` + ``make test-unit``. This
    matches exactly what ci.yml runs on every PR — if it greens
    here, the PR-time gate will green in CI.

    Covers four of the five layered verifications: structure, types
    (tsc ``--checkJs``), html-validate, and jsdom unit specs.
    Browser-level e2e (the fifth layer) is descoped from v1.1 along
    with Playwright; the v1.2 rodney-based replacement will add a
    separate smoke test for that path.
    """
    baked = bake(
        "artifact-bench",
        tmp_path,
        extra_context={"include_example_artifact": "yes"},
    )

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
