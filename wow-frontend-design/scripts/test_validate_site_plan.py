from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate_site_plan.py")
SPEC = importlib.util.spec_from_file_location("validate_site_plan", MODULE_PATH)
assert SPEC and SPEC.loader
validate_site_plan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_site_plan
SPEC.loader.exec_module(validate_site_plan)


class ValidateSitePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scripts = Path(__file__).parent
        cls.base_manifest = json.loads((cls.scripts / "site_manifest.example.json").read_text(encoding="utf-8"))
        cls.base_plan = json.loads((cls.scripts / "wireframe_plan.example.json").read_text(encoding="utf-8"))

    def _write(self, root: Path, manifest: dict | None = None, plan: dict | None = None, *, rehash: bool = True) -> tuple[Path, Path]:
        manifest_value = copy.deepcopy(manifest if manifest is not None else self.base_manifest)
        plan_value = copy.deepcopy(plan if plan is not None else self.base_plan)
        manifest_raw = (json.dumps(manifest_value, ensure_ascii=False, indent=2) + "\n").encode()
        if rehash:
            plan_value["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
        manifest_path = root / "site-manifest.json"
        plan_path = root / "wireframe-plan.json"
        manifest_path.write_bytes(manifest_raw)
        plan_path.write_text(json.dumps(plan_value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return manifest_path, plan_path

    def _findings(self, manifest: dict | None = None, plan: dict | None = None, sitemap_xml: str | None = None, *, rehash: bool = True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path, plan_path = self._write(root, manifest, plan, rehash=rehash)
            sitemap_paths = []
            if sitemap_xml is not None:
                sitemap_path = root / "sitemap.xml"
                sitemap_path.write_text(sitemap_xml, encoding="utf-8")
                sitemap_paths.append(sitemap_path)
            return validate_site_plan.validate_files(manifest_path, plan_path, sitemap_paths)

    @staticmethod
    def _codes(findings) -> set[str]:
        return {item.code for item in findings}

    def test_repository_examples_are_valid(self) -> None:
        findings = validate_site_plan.validate_files(
            self.scripts / "site_manifest.example.json",
            self.scripts / "wireframe_plan.example.json",
            [self.scripts / "sitemap.example.xml"],
        )
        self.assertEqual(findings, [])
        for name in ("site_manifest.schema.json", "wireframe_plan.schema.json"):
            self.assertIsInstance(json.loads((self.scripts / name).read_text(encoding="utf-8")), dict)

    def test_duplicate_route_id_and_normalized_path_are_rejected(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        manifest["routes"].append(copy.deepcopy(manifest["routes"][0]))
        codes = self._codes(self._findings(manifest=manifest))
        self.assertIn("SM_ROUTE_ID_DUPLICATE", codes)
        self.assertIn("SM_ROUTE_PATH_DUPLICATE", codes)

    def test_non_normalized_trailing_slash_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        manifest["routes"][1]["path"] = "/work-orders/"
        self.assertIn("SM_ROUTE_PATH_NOT_NORMALIZED", self._codes(self._findings(manifest=manifest)))

    def test_unknown_parent_and_parent_cycle_are_rejected(self) -> None:
        unknown = copy.deepcopy(self.base_manifest)
        unknown["routes"][1]["parent_id"] = "missing"
        self.assertIn("SM_PARENT_UNKNOWN", self._codes(self._findings(manifest=unknown)))
        cycle = copy.deepcopy(self.base_manifest)
        cycle["routes"][0]["parent_id"] = "work-orders-zh-hant"
        self.assertIn("SM_PARENT_CYCLE", self._codes(self._findings(manifest=cycle)))

    def test_private_route_cannot_be_publicly_linked_indexed_or_sitemapped(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        route = manifest["routes"][1]
        route["navigation"]["publicly_linked"] = True
        route["discovery"]["indexing"] = "index"
        route["discovery"]["include_in_sitemap"] = True
        codes = self._codes(self._findings(manifest=manifest))
        self.assertIn("SM_PRIVATE_ROUTE_PUBLICLY_LINKED", codes)
        self.assertIn("SM_PRIVATE_ROUTE_INDEXABLE", codes)
        self.assertIn("SM_NONINDEXABLE_IN_SITEMAP", codes)

    def test_external_route_and_redirect_targets_are_rejected(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        route = manifest["routes"][1]
        route["path"] = "https://evil.test/work-orders"
        route["lifecycle"] = "redirect"
        route["redirect_to"] = "javascript:alert(1)"
        codes = self._codes(self._findings(manifest=manifest))
        self.assertIn("SM_ROUTE_PATH_EXTERNAL", codes)
        self.assertIn("SM_REDIRECT_TARGET_FORBIDDEN", codes)

    def test_redirect_cycle_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        manifest["routes"][0]["lifecycle"] = "redirect"
        manifest["routes"][0]["redirect_to"] = "work-orders-zh-hant"
        manifest["routes"][1]["lifecycle"] = "redirect"
        manifest["routes"][1]["redirect_to"] = "home-zh-hant"
        self.assertIn("SM_REDIRECT_CYCLE", self._codes(self._findings(manifest=manifest)))

    def test_alternates_must_exist_and_be_reciprocal(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        manifest["routes"][0]["discovery"]["alternate_route_ids"] = ["work-orders-zh-hant"]
        self.assertIn("SM_HREFLANG_RECIPROCAL_MISSING", self._codes(self._findings(manifest=manifest)))
        manifest["routes"][0]["discovery"]["alternate_route_ids"] = ["missing-route"]
        self.assertIn("SM_ALTERNATE_UNKNOWN", self._codes(self._findings(manifest=manifest)))

    def test_manifest_hash_mismatch_is_rejected(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["manifest_sha256"] = "0" * 64
        self.assertIn("X_MANIFEST_HASH_MISMATCH", self._codes(self._findings(plan=plan, rehash=False)))

    def test_implementation_ready_plan_covers_every_active_route_once(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["screens"] = plan["screens"][:1]
        self.assertIn("X_RENDERABLE_ROUTE_PLAN_MISSING", self._codes(self._findings(plan=plan)))
        duplicate = copy.deepcopy(self.base_plan)
        duplicate["screens"].append(copy.deepcopy(duplicate["screens"][1]))
        self.assertIn("X_WIREFRAME_ROUTE_DUPLICATE", self._codes(self._findings(plan=duplicate)))

    def test_required_state_cannot_be_claimed_not_applicable(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["screens"][1]["state_coverage"]["loading"]["status"] = "not_applicable"
        self.assertIn("WF_REQUIRED_STATE_MISSING", self._codes(self._findings(plan=plan)))

    def test_static_trigger_cannot_mask_dynamic_states(self) -> None:
        manifest = copy.deepcopy(self.base_manifest)
        manifest["routes"][1]["state_triggers"].append("static")
        self.assertIn("WF_STATE_TRIGGER_CONFLICT", self._codes(self._findings(manifest=manifest)))

    def test_self_certification_and_unknown_evidence_are_rejected(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["evidence_boundary"]["self_certified"] = True
        plan["screens"][0]["claims"][0]["status"] = "VERIFIED"
        plan["screens"][0]["claims"][0]["evidence_ref"] = "model:self-review"
        codes = self._codes(self._findings(plan=plan))
        self.assertIn("WF_SELF_CERTIFICATION_FORBIDDEN", codes)
        self.assertIn("X_EVIDENCE_REF_UNKNOWN", codes)

    def test_placeholder_content_is_rejected(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["screens"][0]["regions"][0]["content_fixture"] = "Lorem ipsum placeholder"
        self.assertIn("WF_CONTENT_FIXTURE_FAKE", self._codes(self._findings(plan=plan)))

    def test_mobile_scaling_and_stack_only_layouts_are_rejected(self) -> None:
        scaled = copy.deepcopy(self.base_plan)
        scaled["screens"][1]["mobile"]["layout_mode"] = "scale desktop canvas"
        self.assertIn("WF_MOBILE_SCALE_FORBIDDEN", self._codes(self._findings(plan=scaled)))
        stacked = copy.deepcopy(self.base_plan)
        screen = stacked["screens"][1]
        screen["mobile"]["region_order"] = copy.deepcopy(screen["desktop"]["region_order"])
        screen["mobile"]["layout_mode"] = "single stack"
        for transformation in screen["mobile"]["transformations"]:
            transformation["action"] = "preserve"
        self.assertIn("WF_MOBILE_TRANSFORMATION_MISSING", self._codes(self._findings(plan=stacked)))

    def test_touch_fallback_and_all_region_transformations_are_required(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["screens"][1]["interactions"][0]["touch"] = ""
        plan["screens"][1]["mobile"]["transformations"].pop()
        codes = self._codes(self._findings(plan=plan))
        self.assertIn("WF_TOUCH_FALLBACK_MISSING", codes)
        self.assertIn("WF_MOBILE_TRANSFORMATION_MISSING", codes)

    def test_user_flow_rejects_happy_path_only_planning(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        flow = plan["flows"][1]
        flow["alternate_paths"] = []
        flow["exit_states"] = [flow["exit_states"][0]]
        self.assertIn("UF_HAPPY_PATH_ONLY", self._codes(self._findings(plan=plan)))

    def test_user_flow_primary_path_must_terminate_without_a_cycle(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        flow = plan["flows"][1]
        flow["steps"][-1]["next_step_id"] = flow["start_step_id"]
        codes = self._codes(self._findings(plan=plan))
        self.assertIn("UF_PRIMARY_CYCLE", codes)
        self.assertIn("UF_TERMINAL_MISSING", codes)

    def test_user_flow_step_must_reference_a_designed_screen_state(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["flows"][0]["steps"][0]["required_state"] = "error"
        self.assertIn("UF_STEP_STATE_UNCOVERED", self._codes(self._findings(plan=plan)))

    def test_every_active_route_participates_in_a_user_flow(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        plan["flows"] = plan["flows"][:1]
        self.assertIn("X_ACTIVE_ROUTE_FLOW_MISSING", self._codes(self._findings(plan=plan)))

    def test_user_flow_role_and_step_routes_must_match_manifest(self) -> None:
        plan = copy.deepcopy(self.base_plan)
        flow = plan["flows"][1]
        flow["audience_role"] = "訪客"
        flow["steps"][0]["page_id"] = "missing-route"
        codes = self._codes(self._findings(plan=plan))
        self.assertIn("UF_AUDIENCE_ROLE_MISMATCH", codes)
        self.assertIn("UF_STEP_PAGE_UNKNOWN", codes)

    def test_sitemap_must_exactly_match_manifest_and_lastmod(self) -> None:
        xml = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.test/</loc><lastmod>2026-07-13</lastmod></url>
  <url><loc>https://example.test/private</loc></url>
</urlset>"""
        codes = self._codes(self._findings(sitemap_xml=xml))
        self.assertIn("XS_LASTMOD_MISMATCH", codes)
        self.assertIn("XS_MANIFEST_URL_EXTRA", codes)
        missing = """<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>"""
        self.assertIn("XS_MANIFEST_URL_MISSING", self._codes(self._findings(sitemap_xml=missing)))

    def test_sitemap_rejects_doctype_without_parsing_entities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path, plan_path = self._write(root)
            sitemap = root / "sitemap.xml"
            sitemap.write_text('<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]><urlset>&y;</urlset>', encoding="utf-8")
            with self.assertRaises(validate_site_plan.SitePlanInputError):
                validate_site_plan.validate_files(manifest_path, plan_path, [sitemap])

    def test_sitemap_index_uses_only_provided_local_children(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest_path, plan_path = self._write(root)
            index = root / "sitemap.xml"
            child = root / "sitemap-pages.xml"
            index.write_text("""<?xml version="1.0"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>https://example.test/sitemap-pages.xml</loc></sitemap></sitemapindex>""", encoding="utf-8")
            child.write_text("""<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.test/</loc><lastmod>2026-07-14</lastmod></url></urlset>""", encoding="utf-8")
            self.assertEqual(validate_site_plan.validate_files(manifest_path, plan_path, [index, child]), [])


if __name__ == "__main__":
    unittest.main()
