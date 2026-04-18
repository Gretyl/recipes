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
