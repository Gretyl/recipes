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
