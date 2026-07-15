#!/usr/bin/env python3
"""Tests for deterministic v6 repair-ledger assembly."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "evals" / "assemble_product_flow_v6_repaired_ledger.py"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class RepairLedgerAssemblyTests(unittest.TestCase):
    def test_promotes_clean_target_without_changing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root = root / "initial"
            repaired_root = root / "repaired"
            target_name = "codex-gpt-5.4-mini-night-market-allergen-v6"
            source = source_root / target_name
            target = repaired_root / target_name
            source.mkdir(parents=True)
            target.mkdir(parents=True)
            design = b"# Design\n"
            page = b"<!doctype html><title>Night market</title>\n"
            (source / "DESIGN.md").write_bytes(design)
            (source / "index.html").write_bytes(page)
            manifest = {
                "schema_version": 1,
                "run_id": "source-run",
                "status": "completed",
                "started_at": "2026-07-15T00:00:00Z",
                "finished_at": "2026-07-15T00:01:00Z",
                "case": {"id": "night-market-allergen-v6", "target": str(source)},
                "model": {"requested_identifier": "gpt-5.4-mini"},
                "outputs": [
                    {"path": "DESIGN.md", "bytes": len(design), "sha256": digest(design)},
                    {"path": "index.html", "bytes": len(page), "sha256": digest(page)},
                ],
            }
            (source / "run-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            ledger = {
                "schema_version": 1,
                "status": "completed",
                "started_at": "2026-07-15T00:00:00Z",
                "contract": {"artifact_root": str(source_root)},
                "selection": {"count": 1},
                "results": [
                    {
                        "provider": "codex",
                        "model": "gpt-5.4-mini",
                        "case_id": "night-market-allergen-v6",
                        "target": str(source),
                        "status": "completed",
                        "manifest": str(source / "run-manifest.json"),
                    }
                ],
            }
            source_ledger = root / "source.json"
            output = root / "assembled.json"
            source_ledger.write_text(json.dumps(ledger), encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "--source-ledger",
                    str(source_ledger),
                    "--repaired-root",
                    str(repaired_root),
                    "--output",
                    str(output),
                    "--promote-clean",
                    "night-market-allergen-v6",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            assembled = json.loads(output.read_text(encoding="utf-8"))
            promoted = json.loads((target / "run-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(assembled["summary"]["promoted_clean_cases"], 1)
            self.assertEqual(assembled["results"][0]["evidence_mode"], "promoted_clean")
            self.assertEqual(promoted["promotion"]["changed_outputs"], [])
            self.assertEqual((target / "DESIGN.md").read_bytes(), design)
            self.assertEqual((target / "index.html").read_bytes(), page)


if __name__ == "__main__":
    unittest.main()
