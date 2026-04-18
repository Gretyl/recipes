"""Bake-level tests for the artifact-bench cookiecutter template.

These tests programmatically run cookiecutter against the template
with default and custom contexts, then verify the resulting file
trees and file contents.
"""

import pathlib

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
            if line.startswith("verify:") or line.startswith("verify ")
        )
        assert "verify-structure" in verify_line
        assert "verify-types" in verify_line
        assert "verify-html" in verify_line

    def test_makefile_supports_artifact_scoping(self, baked: pathlib.Path) -> None:
        """ARTIFACT= is the per-artifact scoping knob the proposal calls out."""
        makefile = (baked / "Makefile").read_text()
        assert "ARTIFACT" in makefile
        assert "ARTIFACT ?=" in makefile

    def test_package_json_declares_required_devdeps(
        self, baked: pathlib.Path
    ) -> None:
        """The Makefile invokes npx tsc/html-validate/vitest/playwright/tsx — package.json must provide them."""
        import json as _json

        pkg = _json.loads((baked / "package.json").read_text())
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
        import json as _json

        pkg = _json.loads((baked / "package.json").read_text())
        assert "scripts" not in pkg, "package.json must not duplicate Makefile interface"

    def test_tsconfig_enables_checkjs_dom_strict(self, baked: pathlib.Path) -> None:
        """The proposal's authoring story rests on tsc --checkJs over inline JSDoc; DOM lib is required for window/document."""
        import json as _json

        ts = _json.loads((baked / "tsconfig.json").read_text())
        opts = ts.get("compilerOptions", {})
        assert opts.get("checkJs") is True
        assert opts.get("allowJs") is True
        assert opts.get("strict") is True
        assert opts.get("noEmit") is True
        lib = opts.get("lib", [])
        assert any(item == "DOM" or item.lower() == "dom" for item in lib)

    def test_tsconfig_includes_src_shared_scripts(self, baked: pathlib.Path) -> None:
        """The three first-class source roots must be in tsconfig.include."""
        import json as _json

        ts = _json.loads((baked / "tsconfig.json").read_text())
        include = set(ts.get("include", []))
        assert "src/**/*" in include
        assert "shared/**/*" in include
        assert "scripts/**/*" in include

    def test_html_validate_config_extends_recommended(
        self, baked: pathlib.Path
    ) -> None:
        """html-validate is the static-HTML gate — it must extend the recommended preset."""
        import json as _json

        cfg = _json.loads((baked / ".html-validate.json").read_text())
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

    def test_docs_authoring_and_verification_exist(
        self, baked: pathlib.Path
    ) -> None:
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
