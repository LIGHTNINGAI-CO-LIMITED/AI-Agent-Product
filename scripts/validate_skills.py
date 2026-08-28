#!/usr/bin/env python3
"""Validate the Codex skill content in this repository.

This is the repository's lightweight "application": it checks that the skill
packages are well formed and that they follow the project's documented rules.

Checks performed:

1. Every ``*.yaml``/``*.yml`` file parses as valid YAML.
2. Every ``SKILL.md`` has a YAML frontmatter block with the required
   ``name`` and ``description`` keys, and the folder name matches ``name``.
3. No script file keeps obsolete prompt-limit logic. Per ``README.md`` and
   ``codex-skills/ai-agent-product/SKILL.md`` the only supported ceiling is
   ``PROMPT_CHAR_LIMIT = 14500``; legacy validator/script logic that hard-codes
   the deprecated ten-thousand-character ceiling must not be reintroduced.
   Only executable script files are scanned, so Markdown prose that documents
   the deprecation is intentionally not flagged.

Exit code is non-zero if any check fails, so it is safe to use in CI or as a
local preflight.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - guidance for a bare image
    sys.stderr.write(
        "PyYAML is required. Install it with `python3 -m pip install pyyaml`.\n"
    )
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Legacy prompt-limit code patterns that must not reappear. These target
# validator/script *logic*, not prose that merely mentions the obsolete figure
# while explaining that it is deprecated. The ceiling digits are built at
# runtime so this definition does not trip the scan on its own source file.
_LEGACY = "1" + "0000"
FORBIDDEN_PATTERNS = [
    re.compile(r"MAX_PROMPT_CHARS\s*=\s*" + _LEGACY),
    re.compile(r"len\(\s*prompt\s*\)\s*<=?\s*" + _LEGACY),
    re.compile(r"PROMPT_CHAR_LIMIT\s*=\s*" + _LEGACY),
]

# Only executable script files carry prompt-limit *logic*. Markdown and other
# docs legitimately mention the deprecated ceiling to explain the rule.
SCRIPT_SUFFIXES = {".py", ".js", ".ts", ".sh"}


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        files.append(path)
    return files


def check_yaml(files: list[Path], errors: list[str]) -> int:
    checked = 0
    for path in files:
        if path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        checked += 1
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"Invalid YAML in {path.relative_to(REPO_ROOT)}: {exc}")
    return checked


def parse_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    loaded = yaml.safe_load(parts[1])
    return loaded if isinstance(loaded, dict) else None


def check_skills(files: list[Path], errors: list[str]) -> int:
    checked = 0
    for path in files:
        if path.name != "SKILL.md":
            continue
        checked += 1
        rel = path.relative_to(REPO_ROOT)
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter is None:
            errors.append(f"{rel}: missing or invalid YAML frontmatter block")
            continue
        for key in ("name", "description"):
            if not frontmatter.get(key):
                errors.append(f"{rel}: frontmatter is missing required key '{key}'")
        name = frontmatter.get("name")
        if name and name != path.parent.name:
            errors.append(
                f"{rel}: frontmatter name '{name}' does not match folder "
                f"'{path.parent.name}'"
            )
    return checked


def check_prompt_limit(files: list[Path], errors: list[str]) -> int:
    checked = 0
    for path in files:
        if path.suffix.lower() not in SCRIPT_SUFFIXES:
            continue
        checked += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}:{line}: forbidden legacy "
                    f"prompt limit '{match.group(0)}' (use PROMPT_CHAR_LIMIT = 14500)"
                )
    return checked


def main() -> int:
    files = iter_repo_files()
    errors: list[str] = []

    yaml_count = check_yaml(files, errors)
    skill_count = check_skills(files, errors)
    scan_count = check_prompt_limit(files, errors)

    print(f"Scanned {len(files)} files under {REPO_ROOT}")
    print(f"  YAML files validated:        {yaml_count}")
    print(f"  SKILL.md packages validated: {skill_count}")
    print(f"  Files scanned for limits:    {scan_count}")

    if errors:
        print(f"\nFAILED with {len(errors)} problem(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nOK: all skill content is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
