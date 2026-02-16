#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Meld features from source Makefile to target Makefile.

Usage:
  python scripts/meld_makefiles.py temp/baked-example/Makefile.skills temp/baked-example/Makefile
  python scripts/meld_makefiles.py source.mk target.mk --output=prompt | pbcopy
  python scripts/meld_makefiles.py source.mk target.mk --output=json | jq .new_targets

This script analyzes structural differences between two Makefiles and produces
structured output for human review or Claude analysis. It detects new targets,
modified dependencies, variable changes, and help entry additions.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MakefileVariable:
    """Represents a Makefile variable assignment."""

    name: str
    operator: str  # =, :=, ?=, +=, !=
    value: str
    comments: list[str] = field(default_factory=list)


@dataclass
class MakefileTarget:
    """Represents a Makefile target with dependencies and recipe."""

    name: str
    dependencies: list[str]
    recipe: list[str]  # Command lines
    comments: list[str] = field(default_factory=list)


@dataclass
class MakefileStructure:
    """Parsed Makefile structure."""

    variables: dict[str, MakefileVariable]
    targets: dict[str, MakefileTarget]
    phony_targets: set[str]
    default_goal: str | None
    help_entries: dict[str, str] | None = None


@dataclass
class FeatureDiff:
    """Differences between source and target Makefiles."""

    new_targets: list[str]
    modified_targets: list[str]
    removed_targets: list[str]
    new_variables: dict[str, MakefileVariable]
    changed_variables: dict[str, tuple[MakefileVariable, MakefileVariable]]
    new_phony: set[str]
    help_changes: dict[str, str | None] | None = None


# Regex patterns (order matters - check in this sequence)
COMMENT_PATTERN = re.compile(r"^\s*#\s*(.*)$")
PHONY_PATTERN = re.compile(r"^\.PHONY\s*:\s*(.*)$")
DEFAULT_GOAL_PATTERN = re.compile(r"^\.DEFAULT_GOAL\s*:=\s*(.*)$")
VAR_PATTERN = re.compile(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s*(\?=|:=|\+=|!=|=)\s*(.*)$")
TARGET_PATTERN = re.compile(r"^([a-zA-Z_.][a-zA-Z0-9_./%-]*)\s*:(?!=)(.*)$")
RECIPE_PATTERN = re.compile(r"^\t(.*)$")
HELP_PRINTF_PATTERN = re.compile(r'@printf\s+"%-\d+s\s+%s\\n"\s+"([^"]+)"\s+"([^"]*)"')


def parse_makefile(path: Path) -> MakefileStructure:
    """Parse Makefile into structured representation."""
    variables: dict[str, MakefileVariable] = {}
    targets: dict[str, MakefileTarget] = {}
    phony_targets: set[str] = set()
    default_goal: str | None = None
    help_entries: dict[str, str] = {}

    lines = path.read_text(encoding="utf-8").splitlines()
    pending_comments: list[str] = []
    current_target: str | None = None
    logical_line = ""
    line_continuation = False

    for raw_line in lines:
        # Handle line continuations
        if line_continuation:
            logical_line += raw_line
            if not raw_line.endswith("\\"):
                line_continuation = False
                line = logical_line
            else:
                logical_line = logical_line[:-1]  # Remove trailing \
                continue
        else:
            if raw_line.endswith("\\"):
                logical_line = raw_line[:-1]
                line_continuation = True
                continue
            line = raw_line

        # Check for blank lines
        if not line.strip():
            pending_comments.clear()
            continue

        # Check for comments
        if match := COMMENT_PATTERN.match(line):
            pending_comments.append(match.group(1))
            continue

        # Check for .PHONY directive
        if match := PHONY_PATTERN.match(line):
            phony_list = match.group(1).strip()
            for target_name in phony_list.split():
                phony_targets.add(target_name)
            pending_comments.clear()
            continue

        # Check for .DEFAULT_GOAL
        if match := DEFAULT_GOAL_PATTERN.match(line):
            default_goal = match.group(1).strip()
            pending_comments.clear()
            continue

        # Check for recipe line (MUST start with tab)
        if line.startswith("\t"):
            if current_target:
                recipe_line = line[1:]  # Remove leading tab
                targets[current_target].recipe.append(recipe_line)

                # Parse help entries from printf lines in help target
                if current_target == "help" and (help_match := HELP_PRINTF_PATTERN.search(recipe_line)):
                        target_name = help_match.group(1)
                        description = help_match.group(2)
                        # Skip header lines
                        if target_name not in ("Target", "------"):
                            help_entries[target_name] = description
            pending_comments.clear()
            continue

        # Check for variable assignment
        if match := VAR_PATTERN.match(line):
            var_name = match.group(1)
            operator = match.group(2)
            value = match.group(3).strip()
            variables[var_name] = MakefileVariable(
                name=var_name,
                operator=operator,
                value=value,
                comments=pending_comments.copy(),
            )
            pending_comments.clear()
            continue

        # Check for target definition
        if match := TARGET_PATTERN.match(line):
            target_name = match.group(1)
            deps_str = match.group(2).strip()
            dependencies = deps_str.split() if deps_str else []

            targets[target_name] = MakefileTarget(
                name=target_name,
                dependencies=dependencies,
                recipe=[],
                comments=pending_comments.copy(),
            )
            current_target = target_name
            pending_comments.clear()
            continue

        # Unknown line type - clear pending comments
        pending_comments.clear()

    return MakefileStructure(
        variables=variables,
        targets=targets,
        phony_targets=phony_targets,
        default_goal=default_goal,
        help_entries=help_entries if help_entries else None,
    )


def detect_features(src: MakefileStructure, tgt: MakefileStructure) -> FeatureDiff:
    """Identify discrete features in source that are absent/different in target."""
    # Detect new, modified, and removed targets
    new_targets = [name for name in src.targets if name not in tgt.targets]
    removed_targets = [name for name in tgt.targets if name not in src.targets]
    modified_targets = []

    for name in src.targets:
        if name in tgt.targets:
            src_target = src.targets[name]
            tgt_target = tgt.targets[name]
            # Check if dependencies or recipe changed
            if (
                src_target.dependencies != tgt_target.dependencies
                or src_target.recipe != tgt_target.recipe
            ):
                modified_targets.append(name)

    # Detect new and changed variables
    new_variables = {
        name: var for name, var in src.variables.items() if name not in tgt.variables
    }
    changed_variables = {}

    for name in src.variables:
        if name in tgt.variables:
            src_var = src.variables[name]
            tgt_var = tgt.variables[name]
            if src_var.value != tgt_var.value or src_var.operator != tgt_var.operator:
                changed_variables[name] = (tgt_var, src_var)

    # Detect new .PHONY targets
    new_phony = src.phony_targets - tgt.phony_targets

    # Detect help entry changes
    help_changes: dict[str, str | None] | None = None
    if src.help_entries is not None or tgt.help_entries is not None:
        src_help = src.help_entries or {}
        tgt_help = tgt.help_entries or {}
        help_changes = {}

        # New or modified entries
        for target, desc in src_help.items():
            if target not in tgt_help or tgt_help[target] != desc:
                help_changes[target] = desc

        # Removed entries
        for target in tgt_help:
            if target not in src_help:
                help_changes[target] = None

    return FeatureDiff(
        new_targets=new_targets,
        modified_targets=modified_targets,
        removed_targets=removed_targets,
        new_variables=new_variables,
        changed_variables=changed_variables,
        new_phony=new_phony,
        help_changes=help_changes if help_changes else None,
    )


def generate_diff(src_path: Path, tgt_path: Path) -> str:
    """Generate unified diff suitable for Claude analysis."""
    src_lines = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
    tgt_lines = tgt_path.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = difflib.unified_diff(
        tgt_lines, src_lines, fromfile=str(tgt_path), tofile=str(src_path), lineterm=""
    )

    return "".join(diff)


CLAUDE_PROMPT_TEMPLATE = """I'm melding features from a source Makefile into a target Makefile.

SOURCE: {src_path}
TARGET: {tgt_path}

## Detected Features in Source

### New Targets ({new_targets_count})
{new_targets}

### Modified Targets ({modified_targets_count})
{modified_targets}

### Removed Targets ({removed_targets_count})
{removed_targets}

### New Variables ({new_variables_count})
{new_variables}

### Changed Variables ({changed_variables_count})
{changed_variables}

### New .PHONY Declarations ({new_phony_count})
{new_phony}

### Help Entry Changes ({help_changes_count})
{help_changes}

## Full Source File

```makefile
{src_content}
```

## Full Target File

```makefile
{tgt_content}
```

## Unified Diff

```diff
{diff}
```

## Analysis Request

For each feature, evaluate:
1. **Compatibility**: Does target project structure support this? (e.g., does it have skills/ dir?)
2. **Value**: Does this improve target's workflow?
3. **Risk**: Any naming conflicts or dependency issues?
4. **Assignment operators**: Are `?=` vs `:=` vs `=` used correctly?
5. **Recommendation**: Include, exclude, or modify?

Please provide a structured analysis for merging these features.
"""


def build_analysis_prompt(
    src_path: Path,
    tgt_path: Path,
    src_content: str,
    tgt_content: str,
    diff: str,
    features: FeatureDiff,
    src: MakefileStructure,
) -> str:
    """Create structured prompt for Claude using template."""

    # Format new targets
    new_targets_list = []
    for name in features.new_targets:
        target = src.targets[name]
        deps = " ".join(target.dependencies)
        new_targets_list.append(f"  - {name}: {deps if deps else '(no dependencies)'}")
    new_targets_str = "\n".join(new_targets_list) if new_targets_list else "  (none)"

    # Format modified targets
    modified_targets_list = []
    for name in features.modified_targets:
        src_target = src.targets[name]
        deps = " ".join(src_target.dependencies)
        modified_targets_list.append(
            f"  - {name}: {deps if deps else '(no dependencies)'}"
        )
    modified_targets_str = (
        "\n".join(modified_targets_list) if modified_targets_list else "  (none)"
    )

    # Format removed targets
    removed_targets_str = (
        "\n".join(f"  - {name}" for name in features.removed_targets)
        if features.removed_targets
        else "  (none)"
    )

    # Format new variables
    new_variables_list = []
    for name, var in features.new_variables.items():
        operator_desc = {
            "?=": "conditional",
            ":=": "immediate",
            "=": "recursive",
            "+=": "append",
            "!=": "shell",
        }.get(var.operator, var.operator)
        new_variables_list.append(
            f"  - {var.name} {var.operator} {var.value} [{operator_desc} assignment]"
        )
    new_variables_str = (
        "\n".join(new_variables_list) if new_variables_list else "  (none)"
    )

    # Format changed variables
    changed_variables_list = []
    for name, (old_var, new_var) in features.changed_variables.items():
        changed_variables_list.append(f"  - {name}: {old_var.value} → {new_var.value}")
        if old_var.operator != new_var.operator:
            changed_variables_list.append(
                f"    (operator: {old_var.operator} → {new_var.operator})"
            )
    changed_variables_str = (
        "\n".join(changed_variables_list) if changed_variables_list else "  (none)"
    )

    # Format new .PHONY
    new_phony_str = (
        ", ".join(sorted(features.new_phony)) if features.new_phony else "(none)"
    )

    # Format help changes
    help_changes_list = []
    if features.help_changes:
        for target, desc in features.help_changes.items():
            if desc is None:
                help_changes_list.append(f"  - {target}: REMOVED")
            else:
                help_changes_list.append(f"  - {target}: {desc}")
    help_changes_str = "\n".join(help_changes_list) if help_changes_list else "  (none)"

    return CLAUDE_PROMPT_TEMPLATE.format(
        src_path=src_path,
        tgt_path=tgt_path,
        new_targets_count=len(features.new_targets),
        new_targets=new_targets_str,
        modified_targets_count=len(features.modified_targets),
        modified_targets=modified_targets_str,
        removed_targets_count=len(features.removed_targets),
        removed_targets=removed_targets_str,
        new_variables_count=len(features.new_variables),
        new_variables=new_variables_str,
        changed_variables_count=len(features.changed_variables),
        changed_variables=changed_variables_str,
        new_phony_count=len(features.new_phony),
        new_phony=new_phony_str,
        help_changes_count=len(features.help_changes) if features.help_changes else 0,
        help_changes=help_changes_str,
        src_content=src_content,
        tgt_content=tgt_content,
        diff=diff,
    )


def print_analysis(
    features: FeatureDiff, src: MakefileStructure, src_path: Path, tgt_path: Path
) -> None:
    """Display results for user review."""
    print("Makefile Meld Analysis")
    print("=" * 50)
    print()
    print(f"Source: {src_path}")
    print(f"Target: {tgt_path}")
    print()

    # New targets
    if features.new_targets:
        print(f"📌 NEW TARGETS ({len(features.new_targets)})")
        for name in features.new_targets:
            target = src.targets[name]
            # Get description from help if available
            desc = ""
            if src.help_entries and name in src.help_entries:
                desc = f" → {src.help_entries[name]}"
            print(f"  • {name:20s}{desc}")
        print()

    # Modified targets
    if features.modified_targets:
        print(f"🔄 MODIFIED TARGETS ({len(features.modified_targets)})")
        for name in features.modified_targets:
            target = src.targets[name]
            deps = " ".join(target.dependencies) if target.dependencies else "(none)"
            print(f"  • {name:20s} → Dependencies: {deps}")
        print()

    # New variables
    if features.new_variables:
        print(f"➕ NEW VARIABLES ({len(features.new_variables)})")
        for name, var in features.new_variables.items():
            operator_desc = {
                "?=": "conditional assignment",
                ":=": "immediate expansion",
                "=": "recursive expansion",
                "+=": "append",
                "!=": "shell assignment",
            }.get(var.operator, var.operator)
            print(f"  • {var.name} {var.operator} {var.value:40s} [{operator_desc}]")
        print()

    # Changed variables
    if features.changed_variables:
        print(f"⚙️  CHANGED VARIABLES ({len(features.changed_variables)})")
        for name, (old_var, new_var) in features.changed_variables.items():
            print(f"  • {name}: {old_var.value} → {new_var.value}")
            if old_var.operator != new_var.operator:
                print(
                    f"    (operator changed: {old_var.operator} → {new_var.operator})"
                )
        print()

    # New .PHONY
    if features.new_phony:
        print(f"🏷️  NEW .PHONY DECLARATIONS ({len(features.new_phony)})")
        print(f"  • {', '.join(sorted(features.new_phony))}")
        print()

    # Help entries
    if features.help_changes:
        added = [k for k, v in features.help_changes.items() if v is not None]
        removed = [k for k, v in features.help_changes.items() if v is None]
        if added:
            print(f"💡 HELP ENTRIES ADDED ({len(added)})")
            for target in added:
                print(f"  • {target}")
            print()
        if removed:
            print(f"❌ HELP ENTRIES REMOVED ({len(removed)})")
            for target in removed:
                print(f"  • {target}")
            print()

    # Summary
    print("=" * 50)
    print("Run with --output=prompt to generate Claude analysis prompt")
    print("Run with --output=diff to see unified diff")
    print("Run with --output=json for machine-readable output")


def output_json(features: FeatureDiff, src: MakefileStructure) -> None:
    """Output machine-readable JSON representation."""
    data = {
        "new_targets": features.new_targets,
        "modified_targets": features.modified_targets,
        "removed_targets": features.removed_targets,
        "new_variables": {
            name: {
                "operator": var.operator,
                "value": var.value,
                "comments": var.comments,
            }
            for name, var in features.new_variables.items()
        },
        "changed_variables": {
            name: {
                "old_value": old.value,
                "new_value": new.value,
                "old_operator": old.operator,
                "new_operator": new.operator,
            }
            for name, (old, new) in features.changed_variables.items()
        },
        "new_phony": sorted(features.new_phony),
        "help_changes": features.help_changes if features.help_changes else {},
    }
    print(json.dumps(data, indent=2))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Meld features from source Makefile to target Makefile",
        epilog="Example: python scripts/meld_makefiles.py temp/baked-example/Makefile.skills temp/baked-example/Makefile",
    )
    parser.add_argument("source", type=Path, help="Source Makefile with new features")
    parser.add_argument("target", type=Path, help="Target Makefile to compare against")
    parser.add_argument(
        "--output",
        "-o",
        choices=["analysis", "prompt", "diff", "json"],
        default="analysis",
        help="Output format: analysis (human-readable), prompt (for Claude), diff (unified), json (machine-readable)",
    )

    args = parser.parse_args()

    # Validate paths
    src_path: Path = args.source.resolve()
    tgt_path: Path = args.target.resolve()

    if not src_path.exists():
        print(f"Error: Source file not found: {src_path}", file=sys.stderr)
        return 1

    if not tgt_path.exists():
        print(f"Error: Target file not found: {tgt_path}", file=sys.stderr)
        return 1

    # Read file contents
    try:
        src_content = src_path.read_text(encoding="utf-8")
        tgt_content = tgt_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 1

    # Parse Makefiles
    try:
        src = parse_makefile(src_path)
        tgt = parse_makefile(tgt_path)
    except Exception as e:
        print(f"Error parsing Makefiles: {e}", file=sys.stderr)
        return 1

    # Detect features
    features = detect_features(src, tgt)

    # Generate diff
    diff = generate_diff(src_path, tgt_path)

    # Output based on mode
    if args.output == "analysis":
        print_analysis(features, src, src_path, tgt_path)
    elif args.output == "prompt":
        prompt = build_analysis_prompt(
            src_path, tgt_path, src_content, tgt_content, diff, features, src
        )
        print(prompt)
    elif args.output == "diff":
        print(diff)
    elif args.output == "json":
        output_json(features, src)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
