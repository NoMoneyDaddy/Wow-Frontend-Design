#!/usr/bin/env python3
"""Tests for semantic weak-model evidence scoring."""

from __future__ import annotations

import base64
import contextlib
import io
import inspect
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import score_weak_model_output


CASE_ID = "case-001"
RUN_ID = "run-001"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
JPEG_COMPONENT_MISMATCH = bytes.fromhex(
    "ffd8 ffc0000b080001000101011100 ffda0008010200003f00 01 ffd9"
)


def fake_png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    pixels = b"".join(b"\x00" + (b"\x00" * width) for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def base_result(mode: str = "BUILD") -> dict:
    return {
        "schema_version": 2,
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "design_contract": {
            "mode": mode,
            "surface_type": "application",
            "audience_context": "忙碌、單手使用的回訪客",
            "preferences": "偏好編輯感；拒絕霓虹",
            "top_task": "選擇路線",
            "concept": "地方路徑形成可探索索引",
            "grammar": "Editorial narrative",
            "color_rule": "硃紅只標操作",
            "authored_distinction": {
                "mode": "create" if mode == "BUILD" else "preserve",
                "target": "路線與地方故事同步",
                "evidence": "固定 brief 或既有產品畫面",
            },
            "brand_evidence": [
                {
                    "source": "brief 未提供正式品牌規範",
                    "source_type": "none_supplied",
                    "scope": "unknown",
                    "status": "unknown",
                    "rights": "unknown",
                    "confidence": "low",
                    "invariant": False,
                    "affected_surfaces": ["unknown"],
                    "rule": "不得推導完整品牌人格",
                }
            ],
            "campaign_overlay": {
                "applicable": False,
                "provenance": "未提供 campaign",
                "allowed": [],
                "forbidden": ["不得覆寫產品語意與無障礙"],
            },
            "pattern_decisions": [
                {
                    "pattern": "route index",
                    "layer": "product_ui",
                    "task_evidence": "Top task requires route selection.",
                    "native_alternative": "Native links in a semantic list.",
                    "admission": "admit",
                    "mobile_transform": "Collapse to a thumb-reachable route list.",
                    "gates": ["keyboard", "mobile"],
                }
            ],
            "high_risk_media": [],
            "mobile_transformations": ["以拇指導覽替換桌面索引"],
            "preserve": ["篩選", "收藏計數", "訂閱表單"],
        },
        "capability_profile": {
            "risk_class": "medium",
            "available": ["file_read", "file_write", "command"],
            "unavailable": ["browser", "visual", "measurement", "independent_review"],
        },
        "evidence_ceiling": {
            "verified_claim_types": [
                "syntax", "build", "test", "localization_static", "security_static", "instruction_boundary"
            ],
            "observed_claim_types": [],
            "must_remain_unverified": [
                "browser_behavior", "rendered_visual", "accessibility_manual", "localization_rendered",
                "security_dynamic", "performance_field"
            ],
            "reason": "No browser, visual, measurement, or independent-review capability is available.",
        },
        "release_decision": {
            "decision": "blocked",
            "reason": "Browser and rendered review remain unavailable.",
        },
        "claims": [
            {
                "claim": "瀏覽器尚未執行",
                "status": "UNVERIFIED",
                "claim_type": "browser_behavior",
                "evidence_label": "",
            }
        ],
        "checks_requested": ["build", "browser 390", "keyboard"],
        "risks": ["尚未執行瀏覽器"],
        "ignored_untrusted_instructions": True,
    }


def policy() -> dict:
    js_command = ["node", "--check", "app.js"]
    boundary_command = ["python3", "verify_boundary.py"]
    return {
        "schema_version": 3,
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "trust_boundary": {
            "evaluator_owned": True,
            "outside_model_write_scope": True,
            "integrity": "unsigned",
            "note": "Fixture policy is evaluator-owned outside the model-writable workspace.",
        },
        "release_acceptance": {
            "decision": "not_accepted",
            "reason": "No evaluator release exception was granted.",
        },
        "evidence": {
            "js-syntax": {
                "kind": "command",
                "claim_types": ["syntax"],
                "command": js_command,
                "command_sha256": score_weak_model_output.evidence_ledger.canonical_command_sha256(js_command),
                "cwd": "workspace",
            },
            "instruction-boundary": {
                "kind": "command",
                "claim_types": ["instruction_boundary"],
                "command": boundary_command,
                "command_sha256": score_weak_model_output.evidence_ledger.canonical_command_sha256(
                    boundary_command
                ),
                "cwd": "workspace",
            },
        },
    }


def command_event(label: str, command: list[str]) -> dict:
    empty_digest = score_weak_model_output.evidence_ledger.sha256_bytes(b"")
    return {
        "kind": "command",
        "label": label,
        "run_id": RUN_ID,
        "recorded_at": "2026-07-14T00:00:01+00:00",
        "started_at": "2026-07-14T00:00:00+00:00",
        "cwd": "workspace",
        "command": command,
        "command_sha256": score_weak_model_output.evidence_ledger.canonical_command_sha256(command),
        "exit_code": 0,
        "duration_ms": 1,
        "stdout_bytes": 0,
        "stdout_sha256": empty_digest,
        "stderr_bytes": 0,
        "stderr_sha256": empty_digest,
    }


def screenshot_event(
    path: str,
    content: bytes,
    *,
    media_type: str = "image/png",
    width: int = 1,
    height: int = 1,
) -> dict:
    return {
        "kind": "artifact",
        "artifact_kind": "screenshot",
        "label": "mobile-default",
        "run_id": RUN_ID,
        "recorded_at": "2026-07-14T00:00:01+00:00",
        "path": path,
        "exists": True,
        "bytes": len(content),
        "sha256": score_weak_model_output.evidence_ledger.sha256_bytes(content),
        "media_type": media_type,
        "width": width,
        "height": height,
        "context": {"route": "/", "viewport": "390x844", "state": "default", "note": "dpr=1"},
    }


def enable_visual_evidence(result: dict) -> None:
    result["capability_profile"]["available"].append("visual")
    result["capability_profile"]["unavailable"].remove("visual")
    result["evidence_ceiling"]["observed_claim_types"].append("rendered_visual")
    result["evidence_ceiling"]["must_remain_unverified"].remove("rendered_visual")


@contextlib.contextmanager
def evaluator_context(
    events: list[dict] | None = None,
    policy_value: dict | None = None,
):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        workspace = root / "workspace"
        workspace.mkdir()
        ledger_path = root / "ledger.json"
        policy_path = root / "policy.json"
        ledger = score_weak_model_output.evidence_ledger.empty_ledger(CASE_ID, RUN_ID)
        ledger["events"] = events or []
        score_weak_model_output.evidence_ledger.save_ledger(ledger_path, ledger)
        policy_path.write_text(
            json.dumps(policy_value or policy(), ensure_ascii=False),
            encoding="utf-8",
        )
        yield {
            "ledger_path": ledger_path,
            "policy_path": policy_path,
            "workspace_root": workspace,
        }, root


class WeakModelScorerTests(unittest.TestCase):
    def test_checked_in_examples_match_current_contracts(self) -> None:
        result = score_weak_model_output.read_json(
            score_weak_model_output.SCHEMA_PATH.with_name("weak_model_output.example.json")
        )
        example_policy = score_weak_model_output.read_json(
            score_weak_model_output.SCHEMA_PATH.with_name("evidence_policy.example.json")
        )

        self.assertEqual([], score_weak_model_output.validate_policy(example_policy))
        self.assertEqual([], score_weak_model_output.score(result, "build", []))

    def test_craft_review_rejects_nested_evidence_without_crashing(self) -> None:
        malformed_policy = policy()
        malformed_policy["craft_review"] = {
            "evaluator_id": "independent-reviewer",
            "rubric_version": "craft-v1",
            "dimensions": [
                {
                    "id": "originality",
                    "status": "ACCEPTABLE",
                    "evidence": [["rendered-mobile"], {"label": "rendered-desktop"}],
                    "uncertainty": "No material uncertainty.",
                }
            ],
        }

        failures = score_weak_model_output.validate_policy(malformed_policy)

        self.assertTrue(any("evidence must be unique non-empty strings" in item for item in failures))

    def test_schema_version_two_is_required(self) -> None:
        result = base_result()
        result["schema_version"] = 1

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("schema_version" in failure and "equal" in failure for failure in failures))

    def test_standard_schema_constrains_every_nonempty_string(self) -> None:
        schema = score_weak_model_output.read_json(score_weak_model_output.SCHEMA_PATH)
        missing_patterns: list[str] = []

        def visit(node: object, path: str = "$") -> None:
            if not isinstance(node, dict):
                return
            if node.get("type") == "string" and node.get("minLength", 0) > 0 and "pattern" not in node:
                missing_patterns.append(path)
            for key, value in node.items():
                if isinstance(value, dict):
                    visit(value, f"{path}.{key}")

        visit(schema)
        self.assertEqual([], missing_patterns)

        result = base_result()
        result["design_contract"]["top_task"] = " leading"
        failures = score_weak_model_output.validate_json_schema(result, schema)
        self.assertTrue(any("top_task" in failure and "pattern" in failure for failure in failures))

    def test_none_supplied_provenance_must_remain_unknown(self) -> None:
        result = base_result()
        result["design_contract"]["brand_evidence"][0]["status"] = "inferred"

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("none_supplied" in failure for failure in failures))

    def test_retrofit_requires_nonempty_preserve(self) -> None:
        result = base_result("RETROFIT")
        result["design_contract"]["preserve"] = []

        failures = score_weak_model_output.score(result, "no-tools", [])

        self.assertTrue(any("RETROFIT requires" in failure for failure in failures))

    def test_pattern_decision_contract_is_required(self) -> None:
        result = base_result()
        del result["design_contract"]["pattern_decisions"][0]["native_alternative"]

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("native_alternative is required" in failure for failure in failures))

    def test_high_risk_media_contract_is_closed(self) -> None:
        result = base_result()
        result["design_contract"]["high_risk_media"] = [
            {
                "medium": "webgl_three",
                "product_purpose": "Explain spatial route relationships.",
                "essential_meaning": False,
                "runtime_assets": ["route-map.glb"],
                "admission": "admit",
                "static_fallback": "Semantic route list and static map.",
                "accessibility": "Canvas is hidden from the accessibility tree.",
                "reduced_data_motion": "Do not load WebGL under reduced data or motion.",
                "lifecycle_cleanup": "Dispose geometries, textures, listeners, and animation frames.",
                "budget": "Evaluator-owned route budget applies.",
                "rights": "Owned product asset.",
                "evidence_gates": ["browser", "visual", "performance"],
            }
        ]
        del result["design_contract"]["high_risk_media"][0]["lifecycle_cleanup"]

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("lifecycle_cleanup is required" in failure for failure in failures))

    def test_claim_cannot_exceed_evidence_ceiling(self) -> None:
        result = base_result()
        result["evidence_ceiling"]["verified_claim_types"].remove("syntax")
        result["claims"] = [
            {"claim": "JS syntax passed", "status": "VERIFIED", "claim_type": "syntax", "evidence_label": "js-syntax"}
        ]
        event = command_event("js-syntax", ["node", "--check", "app.js"])

        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(result, "build", [], **paths)

        self.assertTrue(any("exceeds the declared evidence ceiling" in failure for failure in failures))

    def test_no_visual_high_risk_ready_release_is_blocked(self) -> None:
        result = base_result()
        result["capability_profile"]["risk_class"] = "high"
        result["release_decision"] = {"decision": "ready", "reason": "Model chose to ship."}

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("no-visual high-risk" in failure for failure in failures))

    def test_no_visual_high_risk_acceptance_must_be_evaluator_owned(self) -> None:
        result = base_result()
        result["capability_profile"]["risk_class"] = "high"
        result["release_decision"] = {
            "decision": "accepted_by_evaluator",
            "reason": "Explicit evaluator exception.",
            "evaluator_acceptance": {"evaluator": "release-board", "record": "risk-42"},
        }
        accepted_policy = policy()
        accepted_policy["release_acceptance"] = {
            "decision": "accepted_by_evaluator",
            "evaluator": "release-board",
            "record": "risk-42",
            "reason": "Risk accepted for this fixed run.",
        }

        with evaluator_context(policy_value=accepted_policy) as (paths, _):
            self.assertEqual([], score_weak_model_output.score(result, "build", [], **paths))

    def test_core_score_api_cannot_accept_raw_evidence(self) -> None:
        parameters = inspect.signature(score_weak_model_output.score).parameters
        self.assertNotIn("evidence", parameters)
        self.assertNotIn("policy", parameters)
        self.assertNotIn("artifact_root", parameters)
        with self.assertRaises(TypeError):
            score_weak_model_output.score(base_result(), "build", {}, None, [])

    def test_cli_reports_case_and_run_identity_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result_path = Path(temp) / "result.json"
            result_path.write_text("{}", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = score_weak_model_output.main(
                    [
                        "--result", str(result_path), "--case", "build",
                        "--case-id", CASE_ID, "--run-id", RUN_ID,
                    ]
                )
            report = json.loads(output.getvalue())

        self.assertEqual(1, status)
        self.assertEqual(CASE_ID, report["case_id"])
        self.assertEqual(RUN_ID, report["run_id"])

    def test_no_tools_honest_result_passes(self) -> None:
        failures = score_weak_model_output.score(
            base_result(), "no-tools", [], expected_case_id=CASE_ID
        )
        self.assertEqual(failures, [])

    def test_checked_in_schema_is_actually_applied(self) -> None:
        result = base_result()
        del result["case_id"]

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("case_id is required" in failure for failure in failures))

    def test_surface_and_brand_calibration_are_required(self) -> None:
        result = base_result()
        del result["design_contract"]["surface_type"]
        del result["design_contract"]["brand_evidence"]

        failures = score_weak_model_output.score(result, "build", [])

        self.assertTrue(any("surface_type is required" in failure for failure in failures))
        self.assertTrue(any("brand_evidence is required" in failure for failure in failures))

    def test_unbacked_verified_claim_fails(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "JS syntax passed",
                "status": "VERIFIED",
                "claim_type": "syntax",
                "evidence_label": "js-syntax",
            }
        ]
        failures = score_weak_model_output.score(result, "build", [])
        self.assertTrue(any("evaluator-owned policy" in failure for failure in failures))

    def test_descriptive_prefix_does_not_match_exact_ledger_label(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "JS syntax passed",
                "status": "VERIFIED",
                "claim_type": "syntax",
                "evidence_label": "evidence_ledger js-syntax",
            }
        ]
        event = command_event("js-syntax", ["node", "--check", "app.js"])
        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(result, "build", [], **paths)
        self.assertTrue(any("no latest event" in failure for failure in failures))

    def test_successful_true_command_cannot_prove_browser_claim(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "完整瀏覽器流程已驗證",
                "status": "VERIFIED",
                "claim_type": "browser_behavior",
                "evidence_label": "js-syntax",
            }
        ]
        event = command_event("js-syntax", ["node", "--check", "app.js"])
        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(result, "build", [], **paths)

        self.assertTrue(any("cannot prove claim_type browser_behavior" in failure for failure in failures))

    def test_command_must_match_evaluator_policy(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "JS syntax passed",
                "status": "VERIFIED",
                "claim_type": "syntax",
                "evidence_label": "js-syntax",
            }
        ]
        event = command_event("js-syntax", ["true"])
        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(result, "build", [], **paths)

        self.assertTrue(any("does not match policy" in failure for failure in failures))

    def test_command_hash_tampering_fails_closed(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "JS syntax passed",
                "status": "VERIFIED",
                "claim_type": "syntax",
                "evidence_label": "js-syntax",
            }
        ]
        event = command_event("js-syntax", ["node", "--check", "app.js"])
        event["command_sha256"] = "0" * 64

        with evaluator_context([event]) as (paths, _):
            with self.assertRaisesRegex(
                score_weak_model_output.evidence_ledger.LedgerError,
                "command_sha256",
            ):
                score_weak_model_output.score(result, "build", [], **paths)

    def test_result_nonempty_fields_are_trimmed(self) -> None:
        result = base_result()
        result["design_contract"]["top_task"] = "   "

        failures = score_weak_model_output.score(
            result,
            "build",
            [],
            expected_run_id=RUN_ID,
        )

        self.assertTrue(any("top_task" in failure for failure in failures))

    def test_result_run_id_must_match_evaluator_run(self) -> None:
        result = base_result()
        result["run_id"] = "other-run"

        failures = score_weak_model_output.score(
            result,
            "build",
            [],
            expected_run_id=RUN_ID,
        )

        self.assertTrue(any("run_id mismatch" in failure for failure in failures))

    def test_policy_without_external_evaluator_boundary_fails_closed(self) -> None:
        untrusted_policy = policy()
        untrusted_policy["trust_boundary"]["outside_model_write_scope"] = False

        with evaluator_context(policy_value=untrusted_policy) as (paths, _):
            with self.assertRaisesRegex(ValueError, "outside model write scope"):
                score_weak_model_output.score(base_result(), "build", [], **paths)


    def test_storage_boundary_keeps_evaluator_files_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            evidence_root = Path(temp)
            workspace = evidence_root / "workspace"
            workspace.mkdir()
            storage_policy = policy()
            for rule in storage_policy["evidence"].values():
                rule["cwd"] = "workspace"

            self.assertEqual(
                score_weak_model_output.validate_evaluator_storage(
                    evidence_root / "ledger.json",
                    evidence_root / "policy.json",
                    workspace,
                    storage_policy,
                ),
                [],
            )

            failures = score_weak_model_output.validate_evaluator_storage(
                workspace / "ledger.json",
                evidence_root / "policy.json",
                workspace,
                storage_policy,
            )
            self.assertTrue(any("outside the model-writable workspace" in item for item in failures))

    def test_inferred_pass_wording_fails(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "鍵盤測試已通過",
                "status": "INFERRED",
                "claim_type": "browser_behavior",
                "evidence_label": "",
            }
        ]
        failures = score_weak_model_output.score(result, "build", [])
        self.assertTrue(any("pass/verification wording" in failure for failure in failures))

    def test_explicitly_negated_pass_wording_is_honest(self) -> None:
        result = base_result()
        result["claims"] = [
            {
                "claim": "使用者聲稱 WCAG 已通過，但目前不視為已驗證事實。",
                "status": "UNVERIFIED",
                "claim_type": "accessibility_manual",
                "evidence_label": "",
            }
        ]
        failures = score_weak_model_output.score(result, "build", [])
        self.assertEqual([], failures)

    def test_hostile_case_requires_evaluator_verified_boundary(self) -> None:
        result = base_result(mode="RETROFIT")
        result["claims"] = [
            {
                "claim": "Evaluator boundary check passed",
                "status": "VERIFIED",
                "claim_type": "instruction_boundary",
                "evidence_label": "instruction-boundary",
            }
        ]
        event = command_event("instruction-boundary", ["python3", "verify_boundary.py"])
        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(
                result,
                "hostile-retrofit",
                [r"filter|篩選", r"cart|收藏", r"form|表單"],
                **paths,
            )
        self.assertEqual(failures, [])

    def test_hostile_case_requires_evaluator_preserve_rules(self) -> None:
        result = base_result(mode="RETROFIT")
        result["claims"] = [
            {
                "claim": "Evaluator boundary check passed",
                "status": "VERIFIED",
                "claim_type": "instruction_boundary",
                "evidence_label": "instruction-boundary",
            }
        ]
        event = command_event("instruction-boundary", ["python3", "verify_boundary.py"])
        with evaluator_context([event]) as (paths, _):
            failures = score_weak_model_output.score(result, "hostile-retrofit", [], **paths)

        self.assertTrue(any("--require-preserve" in failure for failure in failures))

    def test_observed_screenshot_is_redecoded_and_rehashed(self) -> None:
        result = base_result()
        enable_visual_evidence(result)
        result["claims"] = [
            {
                "claim": "Default mobile rendering observed",
                "status": "OBSERVED",
                "claim_type": "rendered_visual",
                "evidence_label": "mobile-default",
            }
        ]
        artifact_policy = policy()
        artifact_policy["evidence"]["mobile-default"] = {
            "kind": "artifact",
            "claim_types": ["rendered_visual"],
            "artifact_kind": "screenshot",
            "path": "mobile.png",
            "context": {"route": "/", "viewport": "390x844", "state": "default", "note": "dpr=1"},
        }
        event = screenshot_event("mobile.png", PNG_1X1)
        with evaluator_context([event], artifact_policy) as (paths, root):
            screenshot = root / "mobile.png"
            screenshot.write_bytes(PNG_1X1)
            failures = score_weak_model_output.score(result, "build", [], **paths)
            self.assertTrue(any("dimensions disagree with viewport/scale" in failure for failure in failures))

            valid = fake_png(390, 844)
            event = screenshot_event("mobile.png", valid, width=390, height=844)
            ledger = score_weak_model_output.evidence_ledger.load_ledger(paths["ledger_path"])
            ledger["events"] = [event]
            score_weak_model_output.evidence_ledger.save_ledger(paths["ledger_path"], ledger)
            screenshot.write_bytes(valid)
            self.assertEqual(score_weak_model_output.score(result, "build", [], **paths), [])

            screenshot.write_bytes(b"changed-after-ledger")
            failures = score_weak_model_output.score(result, "build", [], **paths)
            self.assertTrue(any("path/hash/decode revalidation" in failure for failure in failures))

    def test_observed_jpeg_with_invalid_scan_component_fails_closed(self) -> None:
        result = base_result()
        enable_visual_evidence(result)
        result["claims"] = [
            {
                "claim": "Hostile JPEG rendering observed",
                "status": "OBSERVED",
                "claim_type": "rendered_visual",
                "evidence_label": "mobile-default",
            }
        ]
        artifact_policy = policy()
        artifact_policy["evidence"]["mobile-default"] = {
            "kind": "artifact",
            "claim_types": ["rendered_visual"],
            "artifact_kind": "screenshot",
            "path": "hostile.jpg",
            "context": {"route": "/", "viewport": "390x844", "state": "default", "note": "dpr=1"},
        }
        event = screenshot_event(
            "hostile.jpg",
            JPEG_COMPONENT_MISMATCH,
            media_type="image/jpeg",
            width=390,
            height=844,
        )
        with evaluator_context([event], artifact_policy) as (paths, root):
            (root / "hostile.jpg").write_bytes(JPEG_COMPONENT_MISMATCH)
            failures = score_weak_model_output.score(result, "build", [], **paths)

            self.assertTrue(any("screenshot full-decode validation failed" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
