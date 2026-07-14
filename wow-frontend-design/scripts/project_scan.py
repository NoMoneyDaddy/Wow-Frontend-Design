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
import sys
from collections import Counter
from pathlib import Path
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
}

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


def _is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_NAMES or name.startswith(".env."):
        return True
    return any(part.lower() in {"secrets", "credentials"} for part in path.parts)


def collect_files(root: Path, max_files: int) -> tuple[list[Path], bool]:
    files: list[Path] = []
    truncated = False

    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_dirs = []
        for dirname in sorted(dirs):
            candidate = current_path / dirname
            rel = candidate.relative_to(root).as_posix()
            if candidate.is_symlink():
                continue
            if dirname in IGNORED_DIRS or rel in IGNORED_DIRS:
                continue
            if dirname.startswith(".") and dirname not in {".github", ".storybook"}:
                continue
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for name in sorted(names):
            path = current_path / name
            if path.is_symlink() or _is_sensitive(path):
                continue
            files.append(path)
            if len(files) >= max_files:
                truncated = True
                return files, truncated

    return files, truncated


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_READ_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


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
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            warnings.append(f"{rel} could not be parsed: {error}")
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
    def joined(values: list[str]) -> str:
        return ", ".join(values) if values else "none detected"

    lines = [
        "# Frontend project scan",
        "",
        f"- Root: `{report['root']}`",
        f"- Mode hint: **{report['mode_hint']}**",
        f"- Files scanned: {report['file_count']}" + (" (truncated)" if report["scan_truncated"] else ""),
        f"- Frameworks: {joined(report['frameworks'])}",
        f"- Styling: {joined(report['styling_tools'])}",
        f"- Motion/media runtimes: {joined(report['experience_runtimes'])}",
        f"- Localization: {joined(report['localization_tools'])}",
        f"- Tests: {joined(report['test_tools'])}",
        f"- Document language tags: {joined(report['language_tags'])}",
        "",
        "## Manifests and scripts",
        "",
        f"- Manifests: {joined(report['manifests'])}",
        f"- Lockfiles: {joined(report['lockfiles'])}",
        f"- Package scripts: {joined(report['package_scripts'])}",
        "",
        "## Package evidence",
        "",
    ]
    if report["package_profiles"]:
        for profile in report["package_profiles"]:
            manager = profile["package_manager"] or "not declared"
            versions = ", ".join(
                f"{name}={version}" for name, version in profile["declared_versions"].items()
            ) or "none detected"
            lines.append(
                f"- `{profile['path']}` — package manager: {manager}; declared ranges: {versions}"
            )
    else:
        lines.append("- No package.json evidence detected.")

    lines.extend([
        "",
        "## Frontend signals",
        "",
    ])
    if report["frontend_signals"]:
        lines.extend(f"- {name}: {count}" for name, count in report["frontend_signals"].items())
    else:
        lines.append("- none detected")

    lines.extend(["", "## Inspect next", ""])
    if report["priority_files"]:
        lines.extend(f"- `{path}`" for path in report["priority_files"])
    else:
        lines.append("- No source file candidates detected.")

    lines.extend(["", "## Observations", ""])
    if report["observations"]:
        lines.extend(f"- {item}" for item in report["observations"])
    else:
        lines.append("- No automatic warning signals detected. Manual rendered review is still required.")

    lines.extend(["", f"_Safety: {report['safety']}_"])
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inventory a frontend project before design work.")
    parser.add_argument("root", nargs="?", default=".", help="project root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--max-files", type=int, default=2_500, help="maximum files to inspect (default: 2500)")
    args = parser.parse_args(argv)
    if args.max_files < 1:
        parser.error("--max-files must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    requested_root = Path(args.root).expanduser()
    if requested_root.is_symlink():
        print(f"error: refusing symlink project root: {requested_root}", file=sys.stderr)
        return 2
    root = requested_root.resolve()
    if not root.exists():
        print(f"error: project root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: project root is not a directory: {root}", file=sys.stderr)
        return 2

    report = scan(root, args.max_files)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
