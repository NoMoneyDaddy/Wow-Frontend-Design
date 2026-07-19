#!/usr/bin/env python3
"""Read-only, dependency-free frontend project reconnaissance.

The scanner reports architecture signals without reading dependency trees,
generated output, environment files, or likely secret material.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import unicodedata
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".next",
    ".nuxt",
    ".output",
    ".svelte-kit",
    ".turbo",
    ".vercel",
    "__pycache__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "public/build",
    "storybook-static",
    "target",
    "vendor",
}

SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "secrets.json",
}

TEXT_EXTENSIONS = {
    ".astro",
    ".cshtml",
    ".css",
    ".dart",
    ".ejs",
    ".erb",
    ".ex",
    ".exs",
    ".ftl",
    ".haml",
    ".hbs",
    ".heex",
    ".htm",
    ".html",
    ".java",
    ".js",
    ".jsp",
    ".jspx",
    ".jsx",
    ".kt",
    ".kts",
    ".leex",
    ".liquid",
    ".mdx",
    ".mustache",
    ".njk",
    ".php",
    ".pug",
    ".py",
    ".razor",
    ".rb",
    ".sass",
    ".scss",
    ".slim",
    ".svelte",
    ".swift",
    ".tsx",
    ".twig",
    ".ts",
    ".vm",
    ".vue",
}

CODE_EXTENSIONS = TEXT_EXTENSIONS | {".mjs", ".cjs"}
MAX_READ_BYTES = 512_000
MAX_WALK_DIRECTORIES = 20_000
MAX_DIRECTORY_ENTRIES = 10_000
MAX_JSON_DEPTH = 128

PACKAGE_SIGNALS = {
    "@angular/core": "Angular",
    "@builder.io/qwik": "Qwik",
    "@remix-run/react": "Remix",
    "@solidjs/start": "SolidStart",
    "@sveltejs/kit": "SvelteKit",
    "@vitejs/plugin-react": "Vite",
    "astro": "Astro",
    "gatsby": "Gatsby",
    "next": "Next.js",
    "nuxt": "Nuxt",
    "preact": "Preact",
    "react": "React",
    "solid-js": "SolidJS",
    "svelte": "Svelte",
    "vite": "Vite",
    "vue": "Vue",
}

STYLING_SIGNALS = {
    "@emotion/react": "Emotion",
    "@pandacss/dev": "Panda CSS",
    "@stitches/react": "Stitches",
    "@tailwindcss/vite": "Tailwind CSS",
    "less": "Less",
    "sass": "Sass/SCSS",
    "styled-components": "styled-components",
    "tailwindcss": "Tailwind CSS",
    "unocss": "UnoCSS",
}

EXPERIENCE_RUNTIME_SIGNALS = {
    "@babylonjs/core": "Babylon.js",
    "@lottiefiles/dotlottie-web": "dotLottie",
    "@pixi/react": "PixiJS",
    "@react-three/fiber": "React Three Fiber",
    "@remotion/player": "Remotion Player",
    "@rive-app/canvas": "Rive",
    "@rive-app/react-canvas": "Rive",
    "@studio-freight/lenis": "Lenis",
    "framer-motion": "Motion",
    "gsap": "GSAP",
    "howler": "Howler",
    "lenis": "Lenis",
    "lottie-web": "Lottie",
    "motion": "Motion",
    "ogl": "OGL",
    "pixi.js": "PixiJS",
    "remotion": "Remotion",
    "three": "Three.js",
    "tone": "Tone.js",
}

I18N_SIGNALS = {
    "@angular/localize": "Angular localization",
    "@formatjs/intl": "FormatJS",
    "@lingui/core": "Lingui",
    "@nuxtjs/i18n": "Nuxt i18n",
    "i18next": "i18next",
    "next-intl": "next-intl",
    "next-i18next": "next-i18next",
    "react-intl": "React Intl",
    "react-i18next": "react-i18next",
    "vue-i18n": "Vue I18n",
}

TEST_SIGNALS = {
    "@playwright/test": "Playwright",
    "@testing-library/react": "Testing Library",
    "@testing-library/vue": "Testing Library",
    "cypress": "Cypress",
    "jest": "Jest",
    "storybook": "Storybook",
    "vitest": "Vitest",
}

LINT_SIGNALS = {
    "@biomejs/biome": "biome",
    "eslint": "eslint",
    "stylelint": "stylelint",
}

LINT_CONFIG_TOOLS = {
    **{name: "biome" for name in (".biome.json", ".biome.jsonc", "biome.json", "biome.jsonc")},
    **{
        name: "eslint"
        for name in (
            ".eslintrc", ".eslintrc.cjs", ".eslintrc.js", ".eslintrc.json", ".eslintrc.mjs",
            ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.cjs", "eslint.config.cts",
            "eslint.config.js", "eslint.config.mjs", "eslint.config.mts", "eslint.config.ts",
        )
    },
    **{
        name: "stylelint"
        for name in (
            ".stylelintrc", ".stylelintrc.cjs", ".stylelintrc.js", ".stylelintrc.json",
            ".stylelintrc.mjs", ".stylelintrc.yaml", ".stylelintrc.yml",
            "stylelint.config.cjs", "stylelint.config.js", "stylelint.config.mjs",
        )
    },
}

LINT_CONFIG_NAMES = set(LINT_CONFIG_TOOLS)

LINT_PACKAGE_CONFIG_KEYS = {
    "eslint": "eslintConfig",
    "stylelint": "stylelint",
}

LINT_CLAIM_BOUNDARY = (
    "Discovery only; local binary, resolved version, config loading, parser/plugins, "
    "cwd, scope, command safety and diagnostics remain unverified."
)

MANIFEST_NAMES = {
    "DESIGN.md",
    "Gemfile",
    "Package.swift",
    "angular.json",
    "astro.config.js",
    "astro.config.mjs",
    "astro.config.ts",
    "composer.json",
    "build.gradle",
    "build.gradle.kts",
    "deno.json",
    "gatsby-config.js",
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
    "nuxt.config.js",
    "nuxt.config.ts",
    "nx.json",
    "package.json",
    "pom.xml",
    "pnpm-workspace.yaml",
    "pubspec.yaml",
    "pyproject.toml",
    "requirements.txt",
    "site-manifest.json",
    "svelte.config.js",
    "tailwind.config.js",
    "tailwind.config.ts",
    "turbo.json",
    "vite.config.js",
    "vite.config.ts",
    "wireframe-plan.json",
} | LINT_CONFIG_NAMES

LOCKFILE_NAMES = {
    "Gemfile.lock",
    "Package.resolved",
    "Podfile.lock",
    "bun.lock",
    "bun.lockb",
    "composer.lock",
    "deno.lock",
    "gradle.lockfile",
    "package-lock.json",
    "pnpm-lock.yaml",
    "pubspec.lock",
    "yarn.lock",
}

RELEVANT_PACKAGE_SIGNALS = set().union(
    PACKAGE_SIGNALS,
    STYLING_SIGNALS,
    EXPERIENCE_RUNTIME_SIGNALS,
    I18N_SIGNALS,
    TEST_SIGNALS,
    LINT_SIGNALS,
)

INSTRUCTION_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "copilot-instructions.md",
}

ENTRY_PATTERNS = (
    re.compile(r"(^|/)(app|src)/(layout|page|main|app|index)\.(astro|[cm]?[jt]sx?|svelte|vue)$"),
    re.compile(r"(^|/)(pages|routes)/.+\.(astro|[cm]?[jt]sx?|svelte|vue)$"),
    re.compile(r"(^|/)(index|main|app)\.(html?|[cm]?[jt]sx?)$"),
    re.compile(r"(^|/)(globals?|styles?|app)\.(css|scss|sass)$"),
)

BRAND_EVIDENCE_LIMIT = 48
BRAND_GUIDANCE_NAMES = {
    "brand.md",
    "branding.md",
    "brand-book.md",
    "brand-book.pdf",
    "brand-guide.md",
    "brand-guide.pdf",
    "brand-guidelines.md",
    "brand-guidelines.pdf",
    "brandbook.md",
    "brandbook.pdf",
}
IDENTITY_ASSET_EXTENSIONS = {".avif", ".gif", ".ico", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
FONT_ASSET_EXTENSIONS = {".otf", ".ttf", ".woff", ".woff2"}
CAMPAIGN_ASSET_EXTENSIONS = IDENTITY_ASSET_EXTENSIONS | FONT_ASSET_EXTENSIONS | {".mp4", ".webm"}
CAMPAIGN_PATH_PARTS = {"campaign", "campaigns"}
TOKEN_SOURCE_EXTENSIONS = CODE_EXTENSIONS | {".json", ".tokens", ".yaml", ".yml"}
TOKEN_SOURCE_NAME = re.compile(r"(?:^|[._-])(?:design[._-]?)?tokens?(?:[._-]|$)|(?:^|[._-])theme(?:[._-]|$)")
IDENTITY_ASSET_NAME = re.compile(
    r"(?:^|[._-])(?:brandmark|favicon|logo|logomark|wordmark)(?:[._-]|$)"
)

BRAND_EVIDENCE_BOUNDARY = (
    "Filename and path discovery only; a candidate does not establish approval, ownership, "
    "currentness, rights, scope, or a reusable brand invariant. Inspect the source and classify "
    "it as explicit, observed, inferred, inherited, or unknown before use."
)


def _is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_NAMES or name.startswith(".env."):
        return True
    return any(part.lower() in {"secrets", "credentials"} for part in path.parts)


class ProjectRootError(ValueError):
    """Raised when a requested project root crosses its authorized boundary."""


class UnsafeProjectFileError(ValueError):
    """Raised when a project file is not a bounded regular file."""


def resolve_project_root(requested: Path, authorized: Path) -> Path:
    """Resolve a real project directory contained by an explicit authorized root."""
    requested_absolute = Path(os.path.abspath(requested.expanduser()))
    authorized_absolute = Path(os.path.abspath(authorized.expanduser()))
    if authorized_absolute.is_symlink():
        raise ProjectRootError(f"authorized root must not be a symlink: {authorized_absolute}")
    if not authorized_absolute.is_dir():
        raise ProjectRootError(f"authorized root must be a real directory: {authorized_absolute}")

    try:
        relative_requested = requested_absolute.relative_to(authorized_absolute)
    except ValueError as error:
        raise ProjectRootError(
            f"project root escapes authorized root: {requested_absolute}"
        ) from error

    authorized_resolved = authorized_absolute.resolve()
    cursor = authorized_resolved
    for part in relative_requested.parts:
        candidate = cursor / part
        if candidate.is_symlink():
            raise ProjectRootError(f"project root contains a symlink component: {candidate}")
        cursor = candidate

    try:
        root = cursor.resolve(strict=True)
    except OSError as error:
        raise ProjectRootError(f"project root does not exist: {cursor}") from error
    if not root.is_dir():
        raise ProjectRootError(f"project root is not a directory: {root}")
    try:
        root.relative_to(authorized_resolved)
    except ValueError as error:
        raise ProjectRootError(f"project root escapes authorized root: {root}") from error
    return root


def _read_bounded_regular_bytes(path: Path, max_bytes: int = MAX_READ_BYTES) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise UnsafeProjectFileError(f"{path} is not a regular file")
        if info.st_size > max_bytes:
            raise UnsafeProjectFileError(f"{path} exceeds {max_bytes} bytes")
        raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise UnsafeProjectFileError(f"{path} exceeds {max_bytes} bytes")
        return raw


def collect_files(
    root: Path,
    max_files: int,
    max_directories: int = MAX_WALK_DIRECTORIES,
    max_directory_entries: int = MAX_DIRECTORY_ENTRIES,
) -> tuple[list[Path], bool]:
    files: list[Path] = []
    visited_directories = 0
    pending = [root]

    while pending:
        current_path = pending.pop()
        visited_directories += 1
        if visited_directories > max_directories:
            return files, True
        directories: list[Path] = []
        regular_files: list[Path] = []
        try:
            with os.scandir(current_path) as entries:
                for entry_index, entry in enumerate(entries, start=1):
                    if entry_index > max_directory_entries:
                        return files, True
                    candidate = Path(entry.path)
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        rel = candidate.relative_to(root).as_posix()
                        if entry.name in IGNORED_DIRS or rel in IGNORED_DIRS:
                            continue
                        if entry.name.startswith(".") and entry.name not in {".github", ".storybook"}:
                            continue
                        directories.append(candidate)
                    elif entry.is_file(follow_symlinks=False) and not _is_sensitive(candidate):
                        regular_files.append(candidate)
        except OSError:
            continue
        remaining_directory_budget = max_directories - visited_directories - len(pending)
        if len(directories) > remaining_directory_budget:
            return files, True
        pending.extend(sorted(directories, reverse=True))
        for path in sorted(regular_files):
            files.append(path)
            if len(files) >= max_files:
                return files, True

    return files, False


def read_text(path: Path) -> str:
    try:
        return _read_bounded_regular_bytes(path).decode("utf-8", errors="ignore")
    except (OSError, UnsafeProjectFileError):
        return ""


def _json_depth_exceeds(value: Any, limit: int = MAX_JSON_DEPTH) -> bool:
    """Return whether a decoded JSON tree exceeds an interpreter-neutral depth."""
    pending: list[tuple[Any, int]] = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        if not isinstance(current, (dict, list)):
            continue
        if depth > limit:
            return True
        children = current.values() if isinstance(current, dict) else current
        pending.extend((child, depth + 1) for child in children)
    return False


def load_packages(root: Path, files: Iterable[Path]) -> tuple[list[tuple[str, dict[str, Any]]], list[str]]:
    packages: list[tuple[str, dict[str, Any]]] = []
    warnings: list[str] = []
    package_paths = sorted(
        (path for path in files if path.name == "package.json"),
        key=lambda path: (len(path.relative_to(root).parts), path.relative_to(root).as_posix()),
    )
    for path in package_paths:
        rel = path.relative_to(root).as_posix()
        try:
            raw = json.loads(_read_bounded_regular_bytes(path).decode("utf-8"))
        except (
            OSError,
            RecursionError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            UnsafeProjectFileError,
        ) as error:
            warnings.append(f"{rel} could not be parsed: {error}")
            continue
        if _json_depth_exceeds(raw):
            warnings.append(
                f"{rel} could not be parsed: JSON nesting exceeds {MAX_JSON_DEPTH} levels"
            )
            continue
        if not isinstance(raw, dict):
            warnings.append(f"{rel} is not a JSON object")
            continue
        packages.append((rel, raw))
    return packages, warnings


def package_names(package: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if isinstance(value, dict):
            names.update(str(name) for name in value)
    return names


def declared_relevant_versions(package: dict[str, Any]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package.get(key, {})
        if not isinstance(value, dict):
            continue
        for name, declared in value.items():
            if name in RELEVANT_PACKAGE_SIGNALS and isinstance(declared, str):
                versions[name] = declared
    return dict(sorted(versions.items()))


def _declared_package_version(package: dict[str, Any], package_name: str) -> str | None:
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        values = package.get(key, {})
        if isinstance(values, dict) and isinstance(values.get(package_name), str):
            return values[package_name]
    return None


def _declared_version_kind(value: str) -> str:
    return "exact" if re.fullmatch(r"v?\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", value) else "range_or_protocol"


def lint_capability_inventory(
    root: Path,
    files: list[Path],
    package_files: list[tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Inventory untrusted lint declarations without loading configs or commands."""
    config_sources: dict[str, list[str]] = {tool: [] for tool in LINT_SIGNALS.values()}
    for path in files:
        tool = LINT_CONFIG_TOOLS.get(path.name)
        if tool:
            config_sources[tool].append(path.relative_to(root).as_posix())

    declarations: dict[str, list[dict[str, str]]] = {tool: [] for tool in LINT_SIGNALS.values()}
    scripts_by_manifest: dict[str, list[str]] = {}
    for manifest_path, package in package_files:
        parent = Path(manifest_path).parent.as_posix()
        prefix = "" if parent == "." and len(package_files) == 1 else f"{parent}: "
        scripts = package.get("scripts", {})
        lint_names: set[str] = set()
        if isinstance(scripts, dict):
            for name in scripts:
                if isinstance(name, str) and re.search(r"(?:^|:)(?:lint|check)(?::|$)", name, re.IGNORECASE):
                    lint_names.add(f"{prefix}{name}")
        scripts_by_manifest[manifest_path] = sorted(lint_names)
        for package_name, tool in LINT_SIGNALS.items():
            version = _declared_package_version(package, package_name)
            if version is not None:
                declarations[tool].append(
                    {
                        "manifest_path": manifest_path,
                        "package": package_name,
                        "declared_version": version,
                        "declared_version_kind": _declared_version_kind(version),
                    }
                )
        for tool, key in LINT_PACKAGE_CONFIG_KEYS.items():
            if key in package:
                config_sources[tool].append(f"{manifest_path}#{key}")

    inventory: list[dict[str, Any]] = []
    for tool in ("biome", "stylelint", "eslint"):
        sources = sorted(set(config_sources[tool]))
        used_sources: set[str] = set()
        for declaration in sorted(
            declarations[tool], key=lambda item: (item["manifest_path"], item["package"])
        ):
            manifest_path = declaration["manifest_path"]
            package_root = PurePosixPath(manifest_path).parent
            applicable_sources = []
            for source in sources:
                if "#" in source:
                    applies = source.startswith(f"{manifest_path}#")
                else:
                    config_root = PurePosixPath(source).parent
                    applies = config_root == package_root or config_root in package_root.parents
                if applies:
                    applicable_sources.append(source)
                    used_sources.add(source)
            lint_names = scripts_by_manifest.get(manifest_path, [])
            inventory.append(
                {
                    "tool": tool,
                    "declarations": [declaration],
                    "config_sources": applicable_sources,
                    "script_names": lint_names,
                    "status": "runtime_verification_required"
                    if applicable_sources or lint_names
                    else "declaration_only",
                    "claim_boundary": LINT_CLAIM_BOUNDARY,
                }
            )
        unmatched_sources = [source for source in sources if source not in used_sources]
        if unmatched_sources:
            inventory.append(
                {
                    "tool": tool,
                    "declarations": [],
                    "config_sources": unmatched_sources,
                    "script_names": [],
                    "status": "not_eligible",
                    "claim_boundary": LINT_CLAIM_BOUNDARY,
                }
            )
    return inventory


def detect_by_packages(names: set[str], signals: dict[str, str]) -> list[str]:
    return sorted({label for package, label in signals.items() if package in names})


def relative(root: Path, paths: Iterable[Path]) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in paths)


def entry_score(rel: str) -> tuple[int, int, str]:
    score = 50
    lowered = rel.lower()
    if lowered in {"package.json", "composer.json", "pyproject.toml"}:
        score = 0
    elif any(pattern.search(lowered) for pattern in ENTRY_PATTERNS):
        score = 10
    elif any(token in lowered for token in ("router", "routes", "layout", "global", "theme", "tokens", "i18n")):
        score = 20
    elif lowered.endswith((".css", ".scss", ".sass")):
        score = 30
    return score, lowered.count("/"), lowered


def brand_evidence_inventory(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    """List bounded path candidates without interpreting their visual values or authority."""
    candidates: list[dict[str, str]] = []
    kind_priority = {
        "design_contract": 0,
        "brand_guidance": 1,
        "campaign_overlay": 2,
        "token_source": 3,
        "identity_asset": 4,
        "font_asset": 5,
    }

    for path in files:
        rel = path.relative_to(root).as_posix()
        name = path.name.lower()
        suffix = path.suffix.lower()
        parts = {part.lower() for part in path.relative_to(root).parts[:-1]}
        kind: str | None = None
        signal: str | None = None

        is_campaign_path = bool(parts & CAMPAIGN_PATH_PARTS)
        is_token_source = bool(
            (name.endswith(".tokens.json") or suffix == ".tokens")
            or (suffix in TOKEN_SOURCE_EXTENSIONS and TOKEN_SOURCE_NAME.search(name))
        )
        is_identity_asset = suffix in IDENTITY_ASSET_EXTENSIONS and bool(
            IDENTITY_ASSET_NAME.search(name)
        )

        if is_campaign_path and (
            suffix in CAMPAIGN_ASSET_EXTENSIONS
            or is_token_source
            or name in BRAND_GUIDANCE_NAMES
        ):
            kind, signal = "campaign_overlay", "campaign path"
        elif name == "design.md":
            kind, signal = "design_contract", "canonical contract filename"
        elif name in BRAND_GUIDANCE_NAMES:
            kind, signal = "brand_guidance", "brand guidance filename"
        elif is_token_source:
            kind, signal = "token_source", "token or theme filename"
        elif is_identity_asset:
            kind, signal = "identity_asset", "identity asset filename"
        elif suffix in FONT_ASSET_EXTENSIONS:
            kind, signal = "font_asset", "local font file"

        if kind and signal:
            candidates.append({"path": rel, "kind": kind, "signal": signal})

    candidates.sort(key=lambda item: (kind_priority[item["kind"]], item["path"]))
    truncated = len(candidates) > BRAND_EVIDENCE_LIMIT
    return {
        "status": "candidate_only",
        "candidates": candidates[:BRAND_EVIDENCE_LIMIT],
        "truncated": truncated,
        "claim_boundary": BRAND_EVIDENCE_BOUNDARY,
    }


def scan(root: Path, max_files: int = 2_500) -> dict[str, Any]:
    files, truncated = collect_files(root, max_files)
    rel_paths = relative(root, files)
    package_files, warnings = load_packages(root, files)
    packages: set[str] = set()
    for _, package in package_files:
        packages.update(package_names(package))

    extensions = Counter(path.suffix.lower() or "[no extension]" for path in files)
    code_files = [path for path in files if path.suffix.lower() in CODE_EXTENSIONS]
    manifests = [path for path in files if path.name in MANIFEST_NAMES]
    lockfiles = [path for path in files if path.name in LOCKFILE_NAMES]

    frameworks = detect_by_packages(packages, PACKAGE_SIGNALS)
    styling = detect_by_packages(packages, STYLING_SIGNALS)
    experience_runtimes = detect_by_packages(packages, EXPERIENCE_RUNTIME_SIGNALS)
    localization = detect_by_packages(packages, I18N_SIGNALS)
    testing = detect_by_packages(packages, TEST_SIGNALS)

    if not packages:
        if any(path.suffix.lower() == ".vue" for path in files):
            frameworks.append("Vue (file signal)")
        if any(path.suffix.lower() == ".svelte" for path in files):
            frameworks.append("Svelte (file signal)")
        if any(path.suffix.lower() == ".astro" for path in files):
            frameworks.append("Astro (file signal)")
        if any(path.suffix.lower() in {".html", ".htm"} for path in files):
            frameworks.append("HTML (file signal)")

    suffixes = {path.suffix.lower() for path in files}
    names = {path.name for path in files}
    if suffixes & {".cshtml", ".razor"}:
        frameworks.append("ASP.NET/Razor (file signal)")
    if ".erb" in suffixes or "Gemfile" in names:
        frameworks.append("Ruby/Rails templates (file signal)")
    if suffixes & {".jsp", ".jspx"}:
        frameworks.append("JSP (file signal)")
    if suffixes & {".heex", ".leex"}:
        frameworks.append("Phoenix/Elixir templates (file signal)")
    if ".dart" in suffixes or "pubspec.yaml" in names:
        frameworks.append("Dart/Flutter (file signal)")
    if ".swift" in suffixes or "Package.swift" in names:
        frameworks.append("Swift/SwiftUI (file signal)")
    if suffixes & {".kt", ".kts"}:
        frameworks.append("Kotlin/Android (file signal)")

    style_counts = Counter()
    lang_tags: set[str] = set()
    locale_paths: list[str] = []
    animation_signal = False
    viewport_signal = False

    for path in code_files:
        text = read_text(path)
        if not text:
            continue
        lowered = text.lower()
        style_counts["css custom properties"] += len(re.findall(r"--[a-z0-9_-]+\s*:", lowered))
        style_counts["media queries"] += lowered.count("@media")
        style_counts["container queries"] += lowered.count("@container")
        style_counts["fluid clamp()"] += lowered.count("clamp(")
        style_counts["logical properties"] += len(
            re.findall(r"\b(?:margin|padding|border|inset)-(?:inline|block)(?:-(?:start|end))?\b", lowered)
        )
        style_counts["focus-visible"] += lowered.count(":focus-visible")
        style_counts["reduced motion"] += lowered.count("prefers-reduced-motion")
        style_counts["safe area"] += lowered.count("safe-area-inset")
        style_counts["small/dynamic viewport units"] += len(re.findall(r"\d(?:svh|dvh)\b", lowered))
        viewport_signal = viewport_signal or 'name="viewport"' in lowered or "name='viewport'" in lowered
        animation_signal = animation_signal or any(
            signal in lowered
            for signal in ("@keyframes", "animation:", "requestanimationframe", "gsap.", "framer-motion")
        )
        for match in re.findall(r"\blang\s*=\s*['\"]([a-z0-9-]+)['\"]", lowered):
            lang_tags.add(match)

    for rel in rel_paths:
        parts = {part.lower() for part in Path(rel).parts}
        if parts & {"i18n", "lang", "langs", "locale", "locales", "messages", "translations"}:
            locale_paths.append(rel)

    if locale_paths and not localization:
        localization.append("locale/message files (path signal)")

    script_names: list[str] = []
    package_profiles: list[dict[str, Any]] = []
    for rel, package in package_files:
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            scripts = {}
        prefix = "" if rel == "package.json" and len(package_files) == 1 else f"{Path(rel).parent.as_posix()}: "
        script_names.extend(f"{prefix}{name}" for name in sorted(scripts))
        package_profiles.append(
            {
                "path": rel,
                "name": package.get("name") if isinstance(package.get("name"), str) else None,
                "package_manager": package.get("packageManager")
                if isinstance(package.get("packageManager"), str)
                else None,
                "declared_versions": declared_relevant_versions(package),
            }
        )
    lint_tools = lint_capability_inventory(root, files, package_files)
    brand_evidence = brand_evidence_inventory(root, files)
    candidate_pool = [
        rel
        for rel in rel_paths
        if Path(rel).name in MANIFEST_NAMES
        or Path(rel).name in INSTRUCTION_NAMES
        or Path(rel).suffix.lower() in CODE_EXTENSIONS
        or Path(rel).name in {"components.json", "tsconfig.json"}
    ]
    candidate_files = sorted(candidate_pool, key=entry_score)[:24]

    observations: list[str] = []
    if not files:
        observations.append("No project files detected; treat as BUILD mode.")
    elif not code_files:
        observations.append(
            "Project files exist but no recognized frontend source was detected; manual review is required before choosing BUILD or RETROFIT."
        )
    if truncated:
        observations.append(f"Scan stopped at {max_files} files; narrow the root or raise --max-files.")
    if any(path.suffix.lower() in {".html", ".htm"} for path in files) and not viewport_signal:
        observations.append("No viewport meta signal found in scanned HTML/template files.")
    if animation_signal and style_counts["reduced motion"] == 0:
        observations.append("Animation signals exist but no prefers-reduced-motion signal was detected.")
    if code_files and not testing:
        observations.append("No common frontend test dependency detected; inspect project-specific scripts and CI.")
    if localization and not lang_tags:
        observations.append("Localization signals exist but no static lang attribute was detected; verify runtime document language updates.")
    if any(tool["status"] in {"declaration_only", "not_eligible"} for tool in lint_tools):
        observations.append(
            "Incomplete lint capability evidence was found; keep the adapter disabled until a same-scope declaration and config or lint script are verified."
        )

    return {
        "root": str(root),
        "mode_hint": "BUILD" if not files else ("RETROFIT" if code_files else "UNKNOWN_REVIEW_REQUIRED"),
        "file_count": len(files),
        "scan_truncated": truncated,
        "frameworks": sorted(set(frameworks)),
        "styling_tools": styling,
        "experience_runtimes": experience_runtimes,
        "localization_tools": localization,
        "test_tools": testing,
        "package_scripts": script_names,
        "package_profiles": package_profiles,
        "lint_tools": lint_tools,
        "brand_evidence": brand_evidence,
        "manifests": relative(root, manifests),
        "lockfiles": relative(root, lockfiles),
        "language_tags": sorted(lang_tags),
        "source_extensions": dict(extensions.most_common(16)),
        "frontend_signals": {key: value for key, value in sorted(style_counts.items()) if value},
        "priority_files": candidate_files,
        "observations": warnings + observations,
        "safety": "Skipped generated/dependency directories, symlinks, environment files, and likely credential paths.",
    }


def render_markdown(report: dict[str, Any]) -> str:
    def literal(value: object) -> str:
        escaped: list[str] = []
        for character in str(value):
            category = unicodedata.category(character)
            if (
                category in {"Cc", "Cf", "Cs", "Zl", "Zp"}
                or character in '\\`*_{}[]<>()#!|&"'
            ):
                escaped.append(f"\\u{ord(character):04x}")
            else:
                escaped.append(character)
        return '"' + "".join(escaped) + '"'

    def joined(values: list[str], *, untrusted: bool = False) -> str:
        if untrusted:
            return ", ".join(literal(value) for value in values) if values else "none detected"
        return ", ".join(values) if values else "none detected"

    lines = [
        "# Frontend project scan",
        "",
        f"- Root: {literal(report['root'])}",
        f"- Mode hint: **{report['mode_hint']}**",
        f"- Files scanned: {report['file_count']}" + (" (truncated)" if report["scan_truncated"] else ""),
        f"- Frameworks: {joined(report['frameworks'])}",
        f"- Styling: {joined(report['styling_tools'])}",
        f"- Motion/media runtimes: {joined(report['experience_runtimes'])}",
        f"- Localization: {joined(report['localization_tools'])}",
        f"- Tests: {joined(report['test_tools'])}",
        f"- Lint inventory: {joined([item['tool'] for item in report['lint_tools']])}",
        f"- Document language tags: {joined(report['language_tags'])}",
        "",
        "## Manifests and scripts",
        "",
        f"- Manifests: {joined(report['manifests'], untrusted=True)}",
        f"- Lockfiles: {joined(report['lockfiles'], untrusted=True)}",
        f"- Package scripts: {joined(report['package_scripts'], untrusted=True)}",
        "",
        "## Package evidence",
        "",
    ]
    if report["package_profiles"]:
        for profile in report["package_profiles"]:
            manager = literal(profile["package_manager"] or "not declared")
            versions = ", ".join(
                f"{literal(name)}={literal(version)}"
                for name, version in profile["declared_versions"].items()
            ) or "none detected"
            lines.append(
                f"- {literal(profile['path'])} — package manager: {manager}; declared ranges: {versions}"
            )
    else:
        lines.append("- No package.json evidence detected.")

    if report["lint_tools"]:
        lines.extend(["", "## Lint capability inventory", ""])
        for tool in report["lint_tools"]:
            lines.append(f"- Tool: {tool['tool']} ({tool['status']})")
            lines.append(f"  - Config sources: {joined(tool['config_sources'], untrusted=True)}")
            lines.append(f"  - Script names: {joined(tool['script_names'], untrusted=True)}")
            declarations = [
                f"{item['manifest_path']}:{item['package']}@{item['declared_version']} ({item['declared_version_kind']})"
                for item in tool["declarations"]
            ]
            lines.append(f"  - Declarations: {joined(declarations, untrusted=True)}")
            lines.append(f"  - Boundary: {tool['claim_boundary']}")

    lines.extend([
        "",
        "## Frontend signals",
        "",
    ])
    if report["frontend_signals"]:
        lines.extend(f"- {name}: {count}" for name, count in report["frontend_signals"].items())
    else:
        lines.append("- none detected")

    lines.extend(["", "## Brand evidence candidates", ""])
    if report["brand_evidence"]["candidates"]:
        for item in report["brand_evidence"]["candidates"]:
            lines.append(
                f"- {literal(item['path'])} — {item['kind']} ({item['signal']})"
            )
        if report["brand_evidence"]["truncated"]:
            lines.append(f"- Candidate list stopped at {BRAND_EVIDENCE_LIMIT} entries.")
    else:
        lines.append("- none detected")
    lines.append(f"- Boundary: {report['brand_evidence']['claim_boundary']}")

    lines.extend(["", "## Inspect next", ""])
    if report["priority_files"]:
        lines.extend(f"- {literal(path)}" for path in report["priority_files"])
    else:
        lines.append("- No source file candidates detected.")

    lines.extend(["", "## Observations", ""])
    if report["observations"]:
        lines.extend(f"- {literal(item)}" for item in report["observations"])
    else:
        lines.append("- No automatic warning signals detected. Manual rendered review is still required.")

    lines.extend(["", f"_Safety: {report['safety']}_"])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inventory a frontend project before design work.")
    parser.add_argument("root", nargs="?", default=".", help="project root (default: current directory)")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="emit machine-readable JSON (default)")
    output.add_argument("--markdown", action="store_true", help="emit human-readable neutralized Markdown")
    parser.add_argument(
        "--authorized-root",
        type=Path,
        help="directory boundary containing the project root (default: current directory)",
    )
    parser.add_argument("--max-files", type=int, default=2_500, help="maximum files to inspect (default: 2500)")
    args = parser.parse_args(argv)
    if args.max_files < 1:
        parser.error("--max-files must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        root = resolve_project_root(
            Path(args.root),
            args.authorized_root if args.authorized_root is not None else Path.cwd(),
        )
    except ProjectRootError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    report = scan(root, args.max_files)
    if args.markdown:
        print(render_markdown(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
