#!/usr/bin/env python3
"""Tests for project_scan.py using isolated temporary projects."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import project_scan


class ProjectScanTests(unittest.TestCase):
    def test_detects_modern_frontend_signals_without_reading_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {"build": "next build", "test": "playwright test"},
                        "packageManager": "pnpm@10.0.0",
                        "dependencies": {
                            "next": "1",
                            "react": "1",
                            "next-intl": "1",
                            "@react-three/fiber": "1",
                            "gsap": "1",
                        },
                        "devDependencies": {"@playwright/test": "1", "tailwindcss": "1"},
                    }
                ),
                encoding="utf-8",
            )
            (root / ".env").write_text("TOP_SECRET=do-not-read", encoding="utf-8")
            (root / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
            (root / "app").mkdir()
            (root / "app" / "page.tsx").write_text(
                '<html lang="zh-Hant"><head><meta name="viewport" content="width=device-width" /></head></html>',
                encoding="utf-8",
            )
            (root / "app" / "globals.css").write_text(
                """
                :root { --ink: #111; }
                main { padding-inline: clamp(1rem, 3vw, 3rem); }
                a:focus-visible { outline: 2px solid; }
                @container (width > 30rem) { main { display: grid; } }
                @media (prefers-reduced-motion: reduce) { * { animation: none; } }
                """,
                encoding="utf-8",
            )

            report = project_scan.scan(root)

            self.assertEqual(report["mode_hint"], "RETROFIT")
            self.assertIn("Next.js", report["frameworks"])
            self.assertIn("React", report["frameworks"])
            self.assertIn("Tailwind CSS", report["styling_tools"])
            self.assertIn("React Three Fiber", report["experience_runtimes"])
            self.assertIn("GSAP", report["experience_runtimes"])
            self.assertIn("next-intl", report["localization_tools"])
            self.assertIn("Playwright", report["test_tools"])
            self.assertIn("pnpm-lock.yaml", report["lockfiles"])
            self.assertEqual(report["package_profiles"][0]["package_manager"], "pnpm@10.0.0")
            self.assertEqual(report["package_profiles"][0]["declared_versions"]["next"], "1")
            self.assertIn("zh-hant", report["language_tags"])
            self.assertEqual(report["frontend_signals"]["reduced motion"], 1)
            self.assertNotIn(".env", report["priority_files"])
            self.assertFalse(any("TOP_SECRET" in str(value) for value in report.values()))

    def test_empty_directory_is_build_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = project_scan.scan(Path(temp))

            self.assertEqual(report["mode_hint"], "BUILD")
            self.assertIn("No project files detected; treat as BUILD mode.", report["observations"])

    def test_existing_razor_project_is_not_misclassified_as_build(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            view = root / "Views" / "Home"
            view.mkdir(parents=True)
            (view / "Index.cshtml").write_text(
                '<main lang="zh-Hant"><h1>既有介面</h1></main>', encoding="utf-8"
            )

            report = project_scan.scan(root)

            self.assertEqual(report["mode_hint"], "RETROFIT")
            self.assertIn("ASP.NET/Razor (file signal)", report["frameworks"])

    def test_unrecognized_nonempty_project_requires_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("existing project", encoding="utf-8")

            report = project_scan.scan(root)

            self.assertEqual(report["mode_hint"], "UNKNOWN_REVIEW_REQUIRED")
            self.assertTrue(any("manual review is required" in item for item in report["observations"]))

    def test_file_limit_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(3):
                (root / f"file-{index}.html").write_text("<main></main>", encoding="utf-8")

            report = project_scan.scan(root, max_files=2)

            self.assertTrue(report["scan_truncated"])
            self.assertEqual(report["file_count"], 2)

    def test_detects_frameworks_in_nested_workspace_packages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "apps" / "web"
            app.mkdir(parents=True)
            (root / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n", encoding="utf-8")
            (root / "site-manifest.json").write_text("{}\n", encoding="utf-8")
            (root / "wireframe-plan.json").write_text("{}\n", encoding="utf-8")
            (root / "DESIGN.md").write_text("# Design system\n", encoding="utf-8")
            (app / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {"build": "vite build"},
                        "dependencies": {"vue": "1", "vue-i18n": "1"},
                        "devDependencies": {"vite": "1"},
                    }
                ),
                encoding="utf-8",
            )
            (app / "main.vue").write_text("<template><main>首頁</main></template>", encoding="utf-8")

            report = project_scan.scan(root)

            self.assertIn("Vue", report["frameworks"])
            self.assertIn("Vite", report["frameworks"])
            self.assertIn("Vue I18n", report["localization_tools"])
            self.assertIn("apps/web: build", report["package_scripts"])
            self.assertIn("pnpm-workspace.yaml", report["manifests"])
            self.assertIn("site-manifest.json", report["manifests"])
            self.assertIn("wireframe-plan.json", report["manifests"])
            self.assertIn("DESIGN.md", report["manifests"])


if __name__ == "__main__":
    unittest.main()
