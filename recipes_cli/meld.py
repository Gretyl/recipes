"""Meld features between files.

Core logic for Makefile structural comparison.
CLI wrapper lives in recipes_cli.tui.cli.
"""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class MeldMakefilesArgs(BaseModel):
    """Validated inputs for the ``meld makefiles`` command."""

    source: Path
    target: Path
    output: Literal["analysis", "prompt", "diff", "json"] = "analysis"


class MakefileVariable(BaseModel):
    """A Makefile variable assignment."""

    name: str
    operator: str  # =, :=, ?=, +=, !=
    value: str
    comments: list[str] = []


class MakefileTarget(BaseModel):
    """A Makefile target with dependencies and recipe."""

    name: str
    dependencies: list[str]
    recipe: list[str]
    comments: list[str] = []


class MakefileStructure(BaseModel):
    """Parsed Makefile structure."""

    variables: dict[str, MakefileVariable]
    targets: dict[str, MakefileTarget]
    phony_targets: set[str]
    default_goal: str | None
    help_entries: dict[str, str] | None = None


class VariableInfo(BaseModel):
    """Compact variable representation for diff output."""

    operator: str
    value: str
    comments: list[str] = []


class VariableChange(BaseModel):
    """A changed variable with old and new values."""

    old_value: str
    new_value: str
    old_operator: str
    new_operator: str


class FeatureDiff(BaseModel):
    """Differences between source and target Makefiles."""

    new_targets: list[str]
    modified_targets: list[str]
    removed_targets: list[str]
    new_variables: dict[str, VariableInfo]
    changed_variables: dict[str, VariableChange]
    new_phony: list[str]
    help_changes: dict[str, str | None] | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

COMMENT_PATTERN = re.compile(r"^\s*#\s*(.*)$")
PHONY_PATTERN = re.compile(r"^\.PHONY\s*:\s*(.*)$")
DEFAULT_GOAL_PATTERN = re.compile(r"^\.DEFAULT_GOAL\s*:=\s*(.*)$")
VAR_PATTERN = re.compile(r"^([A-Za-z_.][A-Za-z0-9_.]*)\s*(\?=|:=|\+=|!=|=)\s*(.*)$")
TARGET_PATTERN = re.compile(r"^([a-zA-Z_.][a-zA-Z0-9_./%-]*)\s*:(?!=)(.*)$")
HELP_PRINTF_PATTERN = re.compile(r'@printf\s+"%-\d+s\s+%s\\n"\s+"([^"]+)"\s+"([^"]*)"')


def _extract_help_entry(
    recipe_line: str, current_target: str, help_entries: dict[str, str]
) -> None:
    """Parse help printf lines from a 'help' target recipe."""
    if current_target != "help":
        return
    if help_match := HELP_PRINTF_PATTERN.search(recipe_line):
        target_name = help_match.group(1)
        description = help_match.group(2)
        if target_name not in ("Target", "------"):
            help_entries[target_name] = description


def parse_makefile(path: Path) -> MakefileStructure:
    """Parse a Makefile into a structured representation."""
    variables: dict[str, MakefileVariable] = {}
    targets: dict[str, MakefileTarget] = {}
    phony_targets: set[str] = set()
    default_goal: str | None = None
    help_entries: dict[str, str] = {}

    lines = path.read_text(encoding="utf-8").splitlines()
    pending_comments: list[str] = []
    current_target: str | None = None

    for line in lines:
        if not line.strip():
            pending_comments.clear()
            continue

        if match := COMMENT_PATTERN.match(line):
            pending_comments.append(match.group(1))
            continue

        if match := PHONY_PATTERN.match(line):
            phony_targets.update(match.group(1).strip().split())
            pending_comments.clear()
            continue

        if match := DEFAULT_GOAL_PATTERN.match(line):
            default_goal = match.group(1).strip()
            pending_comments.clear()
            continue

        if line.startswith("\t"):
            if current_target:
                recipe_line = line[1:]
                targets[current_target].recipe.append(recipe_line)
                _extract_help_entry(recipe_line, current_target, help_entries)
            pending_comments.clear()
            continue

        if match := VAR_PATTERN.match(line):
            var_name = match.group(1)
            variables[var_name] = MakefileVariable(
                name=var_name,
                operator=match.group(2),
                value=match.group(3).strip(),
                comments=pending_comments.copy(),
            )
            pending_comments.clear()
            continue

        if match := TARGET_PATTERN.match(line):
            target_name = match.group(1)
            deps_str = match.group(2).strip()
            targets[target_name] = MakefileTarget(
                name=target_name,
                dependencies=deps_str.split() if deps_str else [],
                recipe=[],
                comments=pending_comments.copy(),
            )
            current_target = target_name
            pending_comments.clear()
            continue

        pending_comments.clear()

    return MakefileStructure(
        variables=variables,
        targets=targets,
        phony_targets=phony_targets,
        default_goal=default_goal,
        help_entries=help_entries if help_entries else None,
    )


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------


def _detect_help_changes(
    src: MakefileStructure, tgt: MakefileStructure
) -> dict[str, str | None] | None:
    """Compute help entry additions, modifications, and removals."""
    if src.help_entries is None and tgt.help_entries is None:
        return None
    src_help = src.help_entries or {}
    tgt_help = tgt.help_entries or {}
    changes: dict[str, str | None] = {}
    for target, desc in src_help.items():
        if target not in tgt_help or tgt_help[target] != desc:
            changes[target] = desc
    for target in tgt_help:
        if target not in src_help:
            changes[target] = None
    return changes if changes else None


def _detect_variable_changes(
    src: MakefileStructure, tgt: MakefileStructure
) -> dict[str, VariableChange]:
    """Find variables that exist in both but differ in value or operator."""
    changed: dict[str, VariableChange] = {}
    for name in src.variables:
        if name in tgt.variables:
            src_var = src.variables[name]
            tgt_var = tgt.variables[name]
            if src_var.value != tgt_var.value or src_var.operator != tgt_var.operator:
                changed[name] = VariableChange(
                    old_value=tgt_var.value,
                    new_value=src_var.value,
                    old_operator=tgt_var.operator,
                    new_operator=src_var.operator,
                )
    return changed


def detect_features(src: MakefileStructure, tgt: MakefileStructure) -> FeatureDiff:
    """Identify discrete features in source that are absent/different in target."""
    new_targets = [name for name in src.targets if name not in tgt.targets]
    removed_targets = [name for name in tgt.targets if name not in src.targets]
    modified_targets: list[str] = []

    for name in src.targets:
        if name in tgt.targets:
            src_target = src.targets[name]
            tgt_target = tgt.targets[name]
            if (
                src_target.dependencies != tgt_target.dependencies
                or src_target.recipe != tgt_target.recipe
            ):
                modified_targets.append(name)

    new_variables: dict[str, VariableInfo] = {
        name: VariableInfo(
            operator=var.operator, value=var.value, comments=var.comments
        )
        for name, var in src.variables.items()
        if name not in tgt.variables
    }

    return FeatureDiff(
        new_targets=new_targets,
        modified_targets=modified_targets,
        removed_targets=removed_targets,
        new_variables=new_variables,
        changed_variables=_detect_variable_changes(src, tgt),
        new_phony=sorted(src.phony_targets - tgt.phony_targets),
        help_changes=_detect_help_changes(src, tgt),
    )


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def generate_diff(src_path: Path, tgt_path: Path) -> str:
    """Generate unified diff between two files."""
    src_lines = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
    tgt_lines = tgt_path.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = difflib.unified_diff(
        tgt_lines, src_lines, fromfile=str(tgt_path), tofile=str(src_path), lineterm=""
    )
    return "".join(diff)


OPERATOR_DESCRIPTIONS = {
    "?=": "conditional assignment",
    ":=": "immediate expansion",
    "=": "recursive expansion",
    "+=": "append",
    "!=": "shell assignment",
}


def _format_targets_section(features: FeatureDiff, src: MakefileStructure) -> list[str]:
    """Format new and modified target sections."""
    lines: list[str] = []
    if features.new_targets:
        lines.append(f"NEW TARGETS ({len(features.new_targets)})")
        for name in features.new_targets:
            desc = ""
            if src.help_entries and name in src.help_entries:
                desc = f" -> {src.help_entries[name]}"
            lines.append(f"  * {name:20s}{desc}")
        lines.append("")

    if features.modified_targets:
        lines.append(f"MODIFIED TARGETS ({len(features.modified_targets)})")
        for name in features.modified_targets:
            target = src.targets[name]
            deps = " ".join(target.dependencies) if target.dependencies else "(none)"
            lines.append(f"  * {name:20s} -> Dependencies: {deps}")
        lines.append("")
    return lines


def _format_variables_section(features: FeatureDiff) -> list[str]:
    """Format new and changed variable sections."""
    lines: list[str] = []
    if features.new_variables:
        lines.append(f"NEW VARIABLES ({len(features.new_variables)})")
        for name, var in features.new_variables.items():
            operator_desc = OPERATOR_DESCRIPTIONS.get(var.operator, var.operator)
            lines.append(f"  * {name} {var.operator} {var.value:40s} [{operator_desc}]")
        lines.append("")

    if features.changed_variables:
        lines.append(f"CHANGED VARIABLES ({len(features.changed_variables)})")
        for name, change in features.changed_variables.items():
            lines.append(f"  * {name}: {change.old_value} -> {change.new_value}")
            if change.old_operator != change.new_operator:
                lines.append(
                    f"    (operator changed: {change.old_operator} -> {change.new_operator})"
                )
        lines.append("")
    return lines


def _format_help_section(features: FeatureDiff) -> list[str]:
    """Format help entry change sections."""
    lines: list[str] = []
    if not features.help_changes:
        return lines
    added = [k for k, v in features.help_changes.items() if v is not None]
    removed = [k for k, v in features.help_changes.items() if v is None]
    if added:
        lines.append(f"HELP ENTRIES ADDED ({len(added)})")
        for entry_name in added:
            lines.append(f"  * {entry_name}")
        lines.append("")
    if removed:
        lines.append(f"HELP ENTRIES REMOVED ({len(removed)})")
        for entry_name in removed:
            lines.append(f"  * {entry_name}")
        lines.append("")
    return lines


def format_analysis(
    features: FeatureDiff,
    src: MakefileStructure,
    src_path: Path,
    tgt_path: Path,
) -> str:
    """Human-readable analysis output."""
    lines: list[str] = [
        "Makefile Meld Analysis",
        "=" * 50,
        "",
        f"Source: {src_path}",
        f"Target: {tgt_path}",
        "",
    ]

    lines.extend(_format_targets_section(features, src))
    lines.extend(_format_variables_section(features))

    if features.new_phony:
        lines.append(f"NEW .PHONY DECLARATIONS ({len(features.new_phony)})")
        lines.append(f"  * {', '.join(features.new_phony)}")
        lines.append("")

    lines.extend(_format_help_section(features))

    lines.append("=" * 50)
    lines.append("Run with --output=prompt to generate Claude analysis prompt")
    lines.append("Run with --output=diff to see unified diff")
    lines.append("Run with --output=json for machine-readable output")
    return "\n".join(lines)


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


def format_prompt(
    features: FeatureDiff,
    src: MakefileStructure,
    src_path: Path,
    tgt_path: Path,
    diff: str,
) -> str:
    """Structured prompt for Claude analysis."""
    new_targets_list = []
    for name in features.new_targets:
        target = src.targets[name]
        deps = " ".join(target.dependencies)
        new_targets_list.append(f"  - {name}: {deps if deps else '(no dependencies)'}")
    new_targets_str = "\n".join(new_targets_list) if new_targets_list else "  (none)"

    modified_targets_list = []
    for name in features.modified_targets:
        target = src.targets[name]
        deps = " ".join(target.dependencies)
        modified_targets_list.append(
            f"  - {name}: {deps if deps else '(no dependencies)'}"
        )
    modified_targets_str = (
        "\n".join(modified_targets_list) if modified_targets_list else "  (none)"
    )

    removed_targets_str = (
        "\n".join(f"  - {name}" for name in features.removed_targets)
        if features.removed_targets
        else "  (none)"
    )

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
            f"  - {name} {var.operator} {var.value} [{operator_desc} assignment]"
        )
    new_variables_str = (
        "\n".join(new_variables_list) if new_variables_list else "  (none)"
    )

    changed_variables_list = []
    for name, change in features.changed_variables.items():
        changed_variables_list.append(
            f"  - {name}: {change.old_value} -> {change.new_value}"
        )
        if change.old_operator != change.new_operator:
            changed_variables_list.append(
                f"    (operator: {change.old_operator} -> {change.new_operator})"
            )
    changed_variables_str = (
        "\n".join(changed_variables_list) if changed_variables_list else "  (none)"
    )

    new_phony_str = ", ".join(features.new_phony) if features.new_phony else "(none)"

    help_changes_list = []
    if features.help_changes:
        for entry_name, desc in features.help_changes.items():
            if desc is None:
                help_changes_list.append(f"  - {entry_name}: REMOVED")
            else:
                help_changes_list.append(f"  - {entry_name}: {desc}")
    help_changes_str = "\n".join(help_changes_list) if help_changes_list else "  (none)"

    src_content = src_path.read_text(encoding="utf-8")
    tgt_content = tgt_path.read_text(encoding="utf-8")

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


def format_json(features: FeatureDiff) -> str:
    """Machine-readable JSON output."""
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
                "old_value": change.old_value,
                "new_value": change.new_value,
                "old_operator": change.old_operator,
                "new_operator": change.new_operator,
            }
            for name, change in features.changed_variables.items()
        },
        "new_phony": features.new_phony,
        "help_changes": features.help_changes if features.help_changes else {},
    }
    return json.dumps(data, indent=2)


def meld_makefiles(args: MeldMakefilesArgs) -> str:
    """Compare two Makefiles and return formatted output.

    Returns the formatted string for the chosen output mode.
    Raises ``SystemExit`` on fatal errors.
    """
    src_path = args.source.resolve()
    tgt_path = args.target.resolve()

    if not src_path.exists():
        raise SystemExit(f"Source file not found: {src_path}")
    if not tgt_path.exists():
        raise SystemExit(f"Target file not found: {tgt_path}")

    src = parse_makefile(src_path)
    tgt = parse_makefile(tgt_path)
    features = detect_features(src, tgt)
    diff = generate_diff(src_path, tgt_path)

    if args.output == "json":
        return format_json(features)
    if args.output == "diff":
        return diff
    if args.output == "prompt":
        return format_prompt(features, src, src_path, tgt_path, diff)
    return format_analysis(features, src, src_path, tgt_path)
