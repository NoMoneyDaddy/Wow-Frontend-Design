#!/usr/bin/env python3
"""Validate a skill package's discovery metadata and safe relative resources."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_NAMES = {".env", ".env.local", "credentials", "credentials.json", "id_rsa", "id_ed25519"}


class InstallabilityError(ValueError):
    """Raised when the checked-in skill cannot be safely discovered or copied."""


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise InstallabilityError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise InstallabilityError("SKILL.md frontmatter is not closed") from error
    values: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"([a-z][a-z0-9-]*):\s*(.+)", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"\'')
    return values


def _ignored_by_git(path: Path, repository_root: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", str(path)],
        cwd=repository_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def validate(skill_root: Path, repository_root: Path | None = None) -> int:
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise InstallabilityError(f"skill root must be a real directory: {skill_root}")
    skill_root = skill_root.resolve()
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file() or skill_file.is_symlink():
        raise InstallabilityError("SKILL.md is missing or a symlink")

    metadata = _frontmatter(skill_file)
    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if NAME.fullmatch(name) is None or name != skill_root.name:
        raise InstallabilityError("frontmatter name must be lowercase kebab-case and match the directory")
    if not 1 <= len(description) <= 1024:
        raise InstallabilityError("frontmatter description must contain 1..1024 characters")
    if metadata.get("license") != "MIT" or not (skill_root / "LICENSE").is_file():
        raise InstallabilityError("MIT frontmatter and bundled LICENSE are required")

    openai = skill_root / "agents" / "openai.yaml"
    if not openai.is_file() or openai.is_symlink():
        raise InstallabilityError("agents/openai.yaml is missing or a symlink")
    openai_text = openai.read_text(encoding="utf-8")
    short = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', openai_text, re.MULTILINE)
    prompt = re.search(r'^\s*default_prompt:\s*"([^"]+)"\s*$', openai_text, re.MULTILINE)
    if short is None or not 25 <= len(short.group(1)) <= 64:
        raise InstallabilityError("openai short_description must contain 25..64 characters")
    if prompt is None or f"${name}" not in prompt.group(1):
        raise InstallabilityError("openai default_prompt must explicitly invoke the skill")

    checked_links = 0
    skill_text = skill_file.read_text(encoding="utf-8")
    for raw_target in LINK.findall(skill_text):
        target = raw_target.split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        resolved = (skill_root / target).resolve()
        try:
            resolved.relative_to(skill_root)
        except ValueError as error:
            raise InstallabilityError(f"relative link escapes skill root: {raw_target}") from error
        if not resolved.exists() or resolved.is_symlink():
            raise InstallabilityError(f"relative link is missing or a symlink: {raw_target}")
        checked_links += 1

    repo = repository_root.resolve() if repository_root else None
    for path in skill_root.rglob("*"):
        if path.is_symlink():
            raise InstallabilityError(f"release skill contains a symlink: {path.relative_to(skill_root)}")
        if not path.is_file():
            continue
        relative = path.relative_to(skill_root)
        forbidden_generated = "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}
        forbidden_secret = path.name.casefold() in FORBIDDEN_NAMES
        if forbidden_generated or forbidden_secret:
            if repo is not None and _ignored_by_git(path, repo):
                continue
            raise InstallabilityError(f"release skill contains forbidden file: {relative}")
    return checked_links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    parser.add_argument("--repository-root", type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.skill.expanduser(), args.repository_root.expanduser() if args.repository_root else None)
    except (InstallabilityError, OSError, UnicodeError) as error:
        print(f"skill package invalid: {error}", file=sys.stderr)
        return 1
    print(f"skill package valid: {count} relative links checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
