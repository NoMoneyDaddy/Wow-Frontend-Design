#!/usr/bin/env python3
"""Tests for final-only current visual evidence capture."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evals" / "capture_current_visual_evidence.cjs"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentVisualEvidenceTests(unittest.TestCase):
    def fixture(self, root: Path, *, html: str | None = None) -> tuple[Path, Path, dict]:
        target = root / "workspace"
        target.mkdir()
        brief = "建立可用且有辨識度的繁體中文產品介面。\n".encode()
        (target / "DESIGN.md").write_text("# Design\n", encoding="utf-8")
        (target / "index.html").write_text(
            html or '<!doctype html><html lang="zh-Hant"><head><title>Current</title></head><body><main><h1>現行輸出</h1><p>Fresh evidence only.</p></main></body></html>',
            encoding="utf-8",
        )
        outputs = []
        for name in ("DESIGN.md", "index.html"):
            path = target / name
            outputs.append({
                "path": name,
                "bytes": path.stat().st_size,
                "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
                "sha256": digest(path),
            })
        manifest = {
            "schema_version": 2,
            "status": "completed",
            "brief": {"bytes": len(brief), "sha256": hashlib.sha256(brief).hexdigest()},
            "skill_snapshot": {"tree_sha256": "a" * 64},
            "outputs": outputs,
        }
        (target / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        case = {
            "schema_version": 1,
            "case_id": "private-validation-case",
            "run_id": "run-001",
            "partition": "validation",
            "brief": manifest["brief"],
            "capture_plan": {
                "locale": "zh-Hant",
                "state": "default",
                "pages": "all_html_outputs",
                "wait_condition": "load+fonts+two-raf+300ms+two-raf",
                "profiles": [
                    {"name": "desktop-default", "viewport": {"width": 1440, "height": 1000}, "reducedMotion": "no-preference", "dpr": 1},
                    {"name": "mobile-default", "viewport": {"width": 390, "height": 844}, "reducedMotion": "reduce", "dpr": 1},
                ],
            },
            "craft": {
                "rubric_version": "wow-core-craft-v1",
                "required_dimensions": ["concept-coherence", "originality", "visual-typography"],
                "feedback_policy": "aggregate-failure-families-only",
            },
        }
        case_path = root / "case.json"
        case_path.write_text(json.dumps(case), encoding="utf-8")
        return target, case_path, case

    def invoke(
        self,
        target: Path,
        case: Path,
        evidence: Path,
        convergence: Path | None = None,
        browser_contract: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = ["node", str(CAPTURE), str(target), str(case), str(evidence)]
        if convergence is not None:
            command.append(str(convergence))
        if browser_contract is not None:
            command.extend(("--browser-contract", str(browser_contract)))
        return subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )

    def consequential_contract(
        self,
        root: Path,
        target: Path,
        case: dict,
        *,
        profile: str = "desktop",
        includes_action: bool = True,
    ) -> Path:
        steps = [
            {"id": "open-visible", "action": "assert", "selector": "#open", "expect": "visible"},
        ]
        if includes_action:
            steps.append({"id": "open-details", "action": "click", "selector": "#open"})
        steps.append({"id": "details-visible", "action": "assert", "selector": "#details", "expect": "visible"})
        payload = {
            "schema_version": 2,
            "cases": [{
                "id": "open-details",
                "page": "index.html",
                "profile": profile,
                "steps": steps,
            }],
        }
        contract = root / "browser-contract.json"
        contract.write_text(json.dumps(payload), encoding="utf-8")
        record = {
            "schema_version": 2,
            "bytes": contract.stat().st_size,
            "sha256": digest(contract),
            "case_count": 1,
            "step_count": len(steps),
        }
        manifest_path = target / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["browser_contract"] = record
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        case["schema_version"] = 2
        case["browser_contract"] = record
        case["capture_plan"]["consequential_state"] = {"contract_case_id": "open-details"}
        return contract

    def motion_contract(self, root: Path, target: Path, case: dict) -> Path:
        payload = {
            "schema_version": 2,
            "cases": [
                {
                    "id": "play-motion",
                    "page": "index.html",
                    "profile": "desktop",
                    "steps": [
                        {"id": "play", "action": "click", "selector": "#play"},
                        {
                            "id": "active",
                            "action": "assert",
                            "selector": "main",
                            "expect": "active-animation-count-between",
                            "min_animations": 1,
                            "max_animations": 8,
                        },
                        {
                            "id": "settled",
                            "action": "assert",
                            "selector": "main",
                            "expect": "animations-settled",
                        },
                        {
                            "id": "final",
                            "action": "assert",
                            "selector": "#final",
                            "expect": "visible",
                        },
                    ],
                },
                {
                    "id": "play-reduced",
                    "page": "index.html",
                    "profile": "mobile",
                    "steps": [
                        {"id": "play", "action": "click", "selector": "#play"},
                        {
                            "id": "inactive",
                            "action": "assert",
                            "selector": "main",
                            "expect": "animations-inactive-for",
                            "duration_ms": 200,
                        },
                        {
                            "id": "final",
                            "action": "assert",
                            "selector": "#final",
                            "expect": "visible",
                        },
                    ],
                },
            ],
        }
        contract = root / "browser-contract.json"
        contract.write_text(json.dumps(payload), encoding="utf-8")
        record = {
            "schema_version": 2,
            "bytes": contract.stat().st_size,
            "sha256": digest(contract),
            "case_count": 2,
            "step_count": 7,
        }
        manifest_path = target / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["browser_contract"] = record
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        case["schema_version"] = 3
        case["browser_contract"] = record
        case["capture_plan"]["motion_sequence"] = {
            "page": "index.html",
            "motion_contract_case_id": "play-motion",
            "reduced_motion_contract_case_id": "play-reduced",
            "offsets_ms": [120, 540, 1250],
        }
        return contract

    def test_captures_exact_fresh_desktop_and_mobile_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(0, completed.returncode, completed.stderr)
            receipt = json.loads((evidence / "capture-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual("captured", receipt["status"])
            self.assertEqual({"desktop-default", "mobile-default"}, {item["profile"] for item in receipt["captures"]})
            self.assertEqual({"1440x1000", "390x844"}, {item["context"]["viewport"] for item in receipt["captures"]})
            self.assertEqual(2, len(list((evidence / "artifacts").glob("*.png"))))
            self.assertFalse((evidence / ".source-snapshot").exists())
            self.assertFalse((evidence / "macro-observations.json").exists())
            self.assertFalse((evidence / "cross-output-template-audit.json").exists())
            self.assertEqual(digest(target / "run-manifest.json"), receipt["source"]["run_manifest_sha256"])
            for item in receipt["captures"]:
                artifact = evidence / item["path"]
                self.assertEqual(item["bytes"], artifact.stat().st_size)
                self.assertEqual(item["sha256"], digest(artifact))

    def test_opt_in_v2_captures_default_matrix_plus_one_contract_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, case = self.fixture(
                root,
                html=(
                    '<!doctype html><html><body><main><h1>State</h1>'
                    '<button id="open" onclick="document.querySelector(\'#details\').hidden=false">Open</button>'
                    '<section id="details" hidden>Details</section></main></body></html>'
                ),
            )
            contract = self.consequential_contract(root, target, case)
            case_path.write_text(json.dumps(case, sort_keys=True), encoding="utf-8")

            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, browser_contract=contract)

            self.assertEqual(0, completed.returncode, completed.stderr)
            receipt = json.loads((evidence / "capture-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(2, receipt["schema_version"])
            defaults = [item for item in receipt["captures"] if item["context"]["state"] == "default"]
            states = [item for item in receipt["captures"] if item["context"]["state"] != "default"]
            self.assertEqual(2, len(defaults))
            self.assertEqual(1, len(states))
            self.assertEqual("index.html", states[0]["page"])
            self.assertEqual("desktop-default", states[0]["profile"])
            self.assertEqual("contract:open-details", states[0]["context"]["state"])
            self.assertEqual(case["browser_contract"], receipt["source"]["browser_contract"])

    def test_opt_in_v3_captures_three_fresh_motion_frames_and_reduced_static(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, case = self.fixture(
                root,
                html=(
                    '<!doctype html><html><head><style>'
                    '#final{opacity:.2} @media(prefers-reduced-motion:reduce){#final{opacity:1}}'
                    '</style></head><body><main><h1>Motion</h1>'
                    '<button id="play" onclick="'
                    "if(!matchMedia('(prefers-reduced-motion: reduce)').matches)"
                    "document.querySelector('#final').animate("
                    "[{transform:'translateX(0px)'},{transform:'translateX(20px)'}],"
                    "{duration:700,fill:'forwards'});"
                    '">Play</button><section id="final">Final</section>'
                    '</main></body></html>'
                ),
            )
            contract = self.motion_contract(root, target, case)
            case_path.write_text(json.dumps(case), encoding="utf-8")

            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, browser_contract=contract)

            self.assertEqual(0, completed.returncode, completed.stderr)
            receipt = json.loads((evidence / "capture-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(3, receipt["schema_version"])
            self.assertEqual(6, len(receipt["captures"]))
            self.assertEqual("allow", receipt["capture_standard"]["motion_evidence_animations"])
            self.assertIn(
                '{ animations: "allow", waitCondition: "contract-replay-complete" }',
                CAPTURE.read_text(encoding="utf-8"),
            )
            motion = receipt["motion_evidence"]
            self.assertEqual(3, len(motion["capture_labels"]["motion_sequence"]))
            self.assertIn(
                motion["capture_labels"]["reduced_motion_static"],
                {item["label"] for item in receipt["captures"]},
            )
            self.assertEqual(
                [
                    "fresh-fixed-request-offset-viewport-frames",
                    "fresh-reduced-motion-static-frame",
                ],
                motion["claim_scope"]["observed"],
            )
            self.assertEqual(
                ["timing", "easing", "spatial-continuity", "runtime-performance", "award-quality"],
                motion["claim_scope"]["not_certified"],
            )
            defaults = [
                item for item in receipt["captures"]
                if item["context"]["state"] == "default"
            ]
            self.assertEqual(2, len(defaults))
            self.assertTrue(all(item["context"]["wait_condition"].startswith("post-trigger+") for item in receipt["captures"][2:5]))
            self.assertEqual(
                "contract:play-reduced:reduced-static",
                receipt["captures"][5]["context"]["state"],
            )

    def test_opt_in_v3_rejects_browser_contract_drift_during_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, case = self.fixture(
                root,
                html=(
                    '<!doctype html><html><body><main><h1>Motion</h1>'
                    '<button id="play" onclick="'
                    "if(!matchMedia('(prefers-reduced-motion: reduce)').matches)"
                    "document.querySelector('#final').animate("
                    "[{opacity:.2},{opacity:1}],{duration:700,fill:'forwards'});"
                    '">Play</button><section id="final">Final</section>'
                    '</main></body></html>'
                ),
            )
            contract = self.motion_contract(root, target, case)
            case_path.write_text(json.dumps(case), encoding="utf-8")
            evidence = root / "evidence"
            process = subprocess.Popen(
                [
                    "node",
                    str(CAPTURE),
                    str(target),
                    str(case_path),
                    str(evidence),
                    "--browser-contract",
                    str(contract),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            deadline = time.monotonic() + 20
            artifacts = evidence / "artifacts"
            while time.monotonic() < deadline and not list(artifacts.glob("*.png")):
                if process.poll() is not None:
                    break
                time.sleep(0.05)
            self.assertIsNone(process.poll(), "capture exited before drift could be injected")
            contract.write_bytes(contract.read_bytes() + b"\n")
            stdout, stderr = process.communicate(timeout=30)

            self.assertEqual("", stdout)
            self.assertEqual(1, process.returncode)
            self.assertIn("drifted during capture", stderr)
            self.assertFalse(evidence.exists())

    def test_opt_in_v2_rejects_invalid_consequential_contract_selection(self) -> None:
        modes = {
            "unknown_case": lambda case, _manifest: case["capture_plan"]["consequential_state"].update(
                {"contract_case_id": "missing-case"}
            ),
            "extra_state_key": lambda case, _manifest: case["capture_plan"]["consequential_state"].update(
                {"selector": "#open"}
            ),
            "case_record_drift": lambda case, _manifest: case["browser_contract"].update({"sha256": "b" * 64}),
            "manifest_record_drift": lambda _case, manifest: manifest["browser_contract"].update({"sha256": "c" * 64}),
        }
        for mode, mutate in modes.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                target, case_path, case = self.fixture(root)
                contract = self.consequential_contract(root, target, case)
                manifest_path = target / "run-manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                mutate(case, manifest)
                case_path.write_text(json.dumps(case), encoding="utf-8")
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

                evidence = root / "evidence"
                completed = self.invoke(target, case_path, evidence, browser_contract=contract)

                self.assertEqual(1, completed.returncode)
                self.assertFalse(evidence.exists())

    def test_opt_in_v2_rejects_actionless_or_unsupported_profile_contract_cases(self) -> None:
        for includes_action, profile in ((False, "desktop"), (True, "narrow")):
            with self.subTest(includes_action=includes_action, profile=profile), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                target, case_path, case = self.fixture(root)
                contract = self.consequential_contract(
                    root, target, case, includes_action=includes_action, profile=profile
                )
                case_path.write_text(json.dumps(case), encoding="utf-8")

                evidence = root / "evidence"
                completed = self.invoke(target, case_path, evidence, browser_contract=contract)

                self.assertEqual(1, completed.returncode)
                self.assertFalse(evidence.exists())

    def test_opt_in_v2_rejects_a_contract_action_that_navigates_away(self) -> None:
        for destination in ("/outside.html", "?state=changed", "#changed"):
            with self.subTest(destination=destination), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                target, case_path, case = self.fixture(
                    root,
                    html=(
                        '<!doctype html><html><body><main><h1>State</h1>'
                        f'<a id="open" href="{destination}">Open</a>'
                        '<section id="details">Details</section></main></body></html>'
                    ),
                )
                contract = self.consequential_contract(root, target, case)
                case_path.write_text(json.dumps(case), encoding="utf-8")

                evidence = root / "evidence"
                completed = self.invoke(
                    target,
                    case_path,
                    evidence,
                    browser_contract=contract,
                )

                self.assertEqual(1, completed.returncode)
                self.assertFalse(evidence.exists())

    def test_explicit_page_set_excludes_other_manifest_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, case = self.fixture(root)
            other = target / "legacy.html"
            other.write_text(
                '<!doctype html><html lang="zh-Hant"><body><main><h1>Legacy</h1></main></body></html>',
                encoding="utf-8",
            )
            manifest_path = target / "run-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            direction_pages = [
                "directions/editorial-index.html",
                "directions/task-led-market.html",
            ]
            for page in direction_pages:
                artifact = target / page
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(
                    f'<!doctype html><html><body><main><h1>{page}</h1></main></body></html>',
                    encoding="utf-8",
                )
                manifest["outputs"].append({
                    "path": page,
                    "bytes": artifact.stat().st_size,
                    "mode": f"{stat.S_IMODE(artifact.stat().st_mode):04o}",
                    "sha256": digest(artifact),
                })
            manifest["outputs"].append({
                "path": "legacy.html",
                "bytes": other.stat().st_size,
                "mode": f"{stat.S_IMODE(other.stat().st_mode):04o}",
                "sha256": digest(other),
            })
            manifest["case"] = {"mode": "retrofit", "lane_contract": "RETROFIT"}
            manifest["seed_snapshot"] = {"files": [], "directories": [], "tree_sha256": "a" * 64}
            manifest["mutation"] = {
                "allowed_changes": ["DESIGN.md", *direction_pages],
                "observed_changes": direction_pages,
                "preserved_directories": 0,
            }
            manifest["html_verification"] = {
                "policy": "draft_direction_subset",
                "pages": direction_pages,
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            case["capture_plan"]["pages"] = {
                "policy": "draft_direction_subset",
                "paths": direction_pages,
            }
            case_path.write_text(json.dumps(case), encoding="utf-8")
            convergence = root / "convergence.json"
            convergence.write_text(
                json.dumps({
                    "schema_version": 1,
                    "cohort_id": "private-validation-case",
                    "surface": "primary",
                    "variants": [
                        {"id": "editorial-index", "page": direction_pages[0]},
                        {"id": "task-led-market", "page": direction_pages[1]},
                    ],
                }),
                encoding="utf-8",
            )

            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, convergence)

            self.assertEqual(0, completed.returncode, completed.stderr)
            receipt = json.loads((evidence / "capture-receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(set(direction_pages), {item["page"] for item in receipt["captures"]})
            self.assertEqual(4, len(receipt["captures"]))

            manifest["html_verification"]["pages"] = [
                direction_pages[0],
                direction_pages[0],
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            rejected_evidence = root / "rejected-evidence"
            rejected = self.invoke(target, case_path, rejected_evidence, convergence)
            self.assertEqual(1, rejected.returncode)
            self.assertIn(
                "not bound to a seeded RETROFIT manifest",
                rejected.stderr,
            )
            self.assertFalse(rejected_evidence.exists())

    def test_explicit_page_set_rejects_unknown_or_duplicate_pages(self) -> None:
        for paths in (
            ["directions/missing.html", "directions/other.html"],
            ["directions/same.html", "directions/same.html"],
            ["../index.html", "directions/other.html"],
        ):
            with self.subTest(paths=paths), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                target, case_path, case = self.fixture(root)
                case["capture_plan"]["pages"] = {
                    "policy": "draft_direction_subset",
                    "paths": paths,
                }
                case_path.write_text(json.dumps(case), encoding="utf-8")
                evidence = root / "evidence"

                completed = self.invoke(target, case_path, evidence)

                self.assertEqual(1, completed.returncode)
                self.assertFalse(evidence.exists())

    def test_existing_evidence_directory_is_never_reused_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            evidence = root / "evidence"
            evidence.mkdir()
            marker = evidence / "old.png"
            marker.write_bytes(b"old")
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("must not already exist", completed.stderr)
            self.assertEqual(b"old", marker.read_bytes())

    def test_oversized_case_is_rejected_before_json_read_or_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(root)
            case_path.write_bytes(b" " * 2_000_001)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("bounded regular non-symlink", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_optional_draft_convergence_uses_the_same_capture_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, _ = self.fixture(root)
            second = target / "other.html"
            second.write_text((target / "index.html").read_text(encoding="utf-8"), encoding="utf-8")
            manifest_path = target / "run-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["outputs"].append({
                "path": "other.html",
                "bytes": second.stat().st_size,
                "mode": f"{stat.S_IMODE(second.stat().st_mode):04o}",
                "sha256": digest(second),
            })
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            convergence = root / "convergence.json"
            convergence.write_text(json.dumps({
                "schema_version": 1,
                "cohort_id": "private-validation-case",
                "surface": "primary",
                "variants": [
                    {"id": "index", "page": "index.html"},
                    {"id": "other", "page": "other.html"},
                ],
            }), encoding="utf-8")
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, convergence)
            self.assertEqual(0, completed.returncode, completed.stderr)
            observations_path = evidence / "macro-observations.json"
            audit_path = evidence / "cross-output-template-audit.json"
            observations = json.loads(observations_path.read_text(encoding="utf-8"))
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual(4, len(observations["observations"]))
            self.assertEqual(digest(observations_path), audit["observations"]["sha256"])
            self.assertEqual("advisories_present", audit["result"]["status"])
            self.assertTrue(audit["result"]["advisories"])
            self.assertEqual(0o600, stat.S_IMODE(observations_path.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(audit_path.stat().st_mode))
            self.assertNotIn(str(root), observations_path.read_text(encoding="utf-8"))
            self.assertNotIn(str(root), audit_path.read_text(encoding="utf-8"))

    def test_draft_convergence_contract_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            target, case_path, _ = self.fixture(root)
            convergence = root / "convergence.json"
            convergence.write_text("{}", encoding="utf-8")
            linked = root / "linked-convergence.json"
            linked.symlink_to(convergence)
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence, linked)
            self.assertEqual(1, completed.returncode)
            self.assertIn("unaliased", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_case_from_a_different_brief_fails_before_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, case = self.fixture(root)
            case["brief"]["sha256"] = "b" * 64
            case_path.write_text(json.dumps(case), encoding="utf-8")
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("case brief does not match", completed.stderr)
            self.assertFalse(evidence.exists())

    def test_failed_fresh_replay_removes_partial_capture_cohort(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, case_path, _ = self.fixture(
                root,
                html='<!doctype html><html lang="zh-Hant"><head><title>X</title></head><body><main><h1>X</h1><img src="https://example.invalid/x.png"></main></body></html>',
            )
            evidence = root / "evidence"
            completed = self.invoke(target, case_path, evidence)
            self.assertEqual(1, completed.returncode)
            self.assertIn("fresh browser replay did not remain clean", completed.stderr)
            self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main()
