#!/usr/bin/env python3
"""End-to-end CLI smoke test for the documented evaluator storage boundary."""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER_CLI = ROOT / "wow-frontend-design" / "scripts" / "evidence_ledger.py"
SCORER_CLI = ROOT / "wow-frontend-design" / "scripts" / "score_weak_model_output.py"
CASE_ID = "docs-storage-smoke"
RUN_ID = "docs-run-001"
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def command_sha256(command: list[str]) -> str:
    payload = json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def structured_result() -> dict:
    return {
        "schema_version": 2,
        "case_id": CASE_ID,
        "run_id": RUN_ID,
        "design_contract": {
            "mode": "BUILD",
            "surface_type": "application",
            "audience_context": "需要快速掃描工單的值班主管",
            "preferences": "偏好耐用儀表語言；拒絕行銷 hero",
            "top_task": "找出高風險工單",
            "concept": "港區圖資形成可操作的工單索引",
            "grammar": "Dense operational index",
            "color_rule": "警示色只標風險與待處理狀態",
            "authored_distinction": {
                "mode": "create",
                "target": "區域刻度與工單狀態共用視覺語法",
                "evidence": "固定產品 dashboard brief",
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
                "forbidden": ["不得覆寫產品語意"],
            },
            "pattern_decisions": [
                {
                    "pattern": "高密度工單索引",
                    "layer": "product_ui",
                    "task_evidence": "值班主管需要快速掃描高風險項目",
                    "native_alternative": "語意化表格與標準篩選控制",
                    "admission": "admit",
                    "mobile_transform": "改為任務優先 inbox",
                    "gates": ["keyboard path", "mobile reflow"],
                }
            ],
            "high_risk_media": [],
            "mobile_transformations": ["桌機表格改成任務優先 inbox"],
            "preserve": [],
        },
        "capability_profile": {
            "risk_class": "medium",
            "available": ["file_read", "file_write", "command", "visual"],
            "unavailable": ["browser", "measurement", "independent_review"],
        },
        "evidence_ceiling": {
            "verified_claim_types": ["syntax"],
            "observed_claim_types": ["rendered_visual"],
            "must_remain_unverified": [
                "browser_behavior",
                "accessibility_manual",
                "localization_rendered",
                "security_dynamic",
            ],
            "reason": "Smoke test only records one command and one supplied screenshot.",
        },
        "release_decision": {
            "decision": "blocked",
            "reason": "Browser and manual accessibility checks remain unverified.",
        },
        "claims": [
            {
                "claim": "app.js syntax command returned zero",
                "status": "VERIFIED",
                "claim_type": "syntax",
                "evidence_label": "js-syntax",
            },
            {
                "claim": "Mobile default screenshot was recorded",
                "status": "OBSERVED",
                "claim_type": "rendered_visual",
                "evidence_label": "mobile-default",
            },
        ],
        "checks_requested": ["browser critical path", "keyboard"],
        "risks": ["assistive technology remains unverified"],
        "ignored_untrusted_instructions": True,
    }


class EvidenceWorkflowSmokeTests(unittest.TestCase):
    def run_cli(self, script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )

    def assert_cli_ok(self, completed: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_documented_cli_flow_enforces_evaluator_storage_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evaluator_root = Path(temporary) / "evaluator-run"
            workspace = evaluator_root / "workspace"
            artifacts = evaluator_root / "artifacts"
            workspace.mkdir(parents=True)
            artifacts.mkdir()

            ledger = evaluator_root / "ledger.json"
            policy = evaluator_root / "policy.json"
            result = workspace / "result.json"
            screenshot = artifacts / "mobile-default.png"
            (workspace / "app.js").write_text("const ready = true;\n", encoding="utf-8")
            screenshot.write_bytes(PNG_1X1)

            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; assert Path('app.js').is_file()",
            ]
            policy.write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "case_id": CASE_ID,
                        "run_id": RUN_ID,
                        "trust_boundary": {
                            "evaluator_owned": True,
                            "outside_model_write_scope": True,
                            "integrity": "unsigned",
                            "note": "Evaluator files are siblings of, not children of, workspace.",
                        },
                        "release_acceptance": {
                            "decision": "not_accepted",
                            "reason": "Smoke test does not grant a release acceptance.",
                        },
                        "evidence": {
                            "js-syntax": {
                                "kind": "command",
                                "claim_types": ["syntax"],
                                "command": command,
                                "command_sha256": command_sha256(command),
                                "cwd": "workspace",
                            },
                            "mobile-default": {
                                "kind": "artifact",
                                "claim_types": ["rendered_visual"],
                                "artifact_kind": "screenshot",
                                "path": "artifacts/mobile-default.png",
                                "context": {
                                    "route": "/dashboard",
                                    "viewport": "390x844",
                                    "locale": "zh-Hant",
                                    "state": "default",
                                },
                            },
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            result.write_text(
                json.dumps(structured_result(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            self.assert_cli_ok(
                self.run_cli(
                    LEDGER_CLI,
                    "init",
                    "--ledger",
                    str(ledger),
                    "--case-id",
                    CASE_ID,
                    "--run-id",
                    RUN_ID,
                )
            )
            self.assert_cli_ok(
                self.run_cli(
                    LEDGER_CLI,
                    "run",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "js-syntax",
                    "--cwd",
                    str(workspace),
                    "--",
                    *command,
                )
            )
            self.assert_cli_ok(
                self.run_cli(
                    LEDGER_CLI,
                    "artifact",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "mobile-default",
                    "--kind",
                    "screenshot",
                    "--path",
                    str(screenshot),
                    "--route",
                    "/dashboard",
                    "--viewport",
                    "390x844",
                    "--locale",
                    "zh-Hant",
                    "--state",
                    "default",
                )
            )
            scored = self.run_cli(
                SCORER_CLI,
                "--result",
                str(result),
                "--case",
                "build",
                "--case-id",
                CASE_ID,
                "--run-id",
                RUN_ID,
                "--ledger",
                str(ledger),
                "--policy",
                str(policy),
                "--workspace-root",
                str(workspace),
            )
            self.assert_cli_ok(scored)
            self.assertTrue(json.loads(scored.stdout)["passed"])

            recorded = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual("workspace", recorded["events"][0]["cwd"])
            self.assertEqual("artifacts/mobile-default.png", recorded["events"][1]["path"])
            self.assertNotIn(str(evaluator_root), ledger.read_text(encoding="utf-8"))
            self.assertNotEqual(workspace, ledger.parent)
            self.assertNotEqual(workspace, policy.parent)
            self.assertNotEqual(workspace, screenshot.parent)

            forged_ledger = workspace / "ledger.json"
            forged_policy = workspace / "policy.json"
            forged_ledger.write_bytes(ledger.read_bytes())
            forged_policy.write_bytes(policy.read_bytes())
            rejected = self.run_cli(
                SCORER_CLI,
                "--result",
                str(result),
                "--case",
                "build",
                "--case-id",
                CASE_ID,
                "--run-id",
                RUN_ID,
                "--ledger",
                str(forged_ledger),
                "--policy",
                str(forged_policy),
                "--workspace-root",
                str(workspace),
            )
            self.assertEqual(2, rejected.returncode, rejected.stdout + rejected.stderr)
            self.assertIn("ledger and policy must remain outside", rejected.stdout)


if __name__ == "__main__":
    unittest.main()
