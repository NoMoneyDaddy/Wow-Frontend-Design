#!/usr/bin/env python3
"""Tests for the persistent Codex resource monitor."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "evals" / "monitor_codex_progress.py"
SPEC = importlib.util.spec_from_file_location("monitor_codex_progress", MODULE_PATH)
assert SPEC and SPEC.loader
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class CodexResourceMonitorTests(unittest.TestCase):
    def test_stage_usage_rejects_symlink_and_non_regular_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            (stage / "ok.txt").write_text("ok", encoding="utf-8")
            self.assertGreaterEqual(monitor.stage_usage_bytes(stage, 4096), 2)
            linked = root / "linked"
            linked.symlink_to(stage, target_is_directory=True)
            with self.assertRaises(monitor.ResourceMonitorError):
                monitor.stage_usage_bytes(linked, 4096)
            (stage / "bad-link").symlink_to(stage / "ok.txt")
            with self.assertRaises(monitor.ResourceMonitorError):
                monitor.stage_usage_bytes(stage, 4096)

    def test_log_quota_terminates_group_and_writes_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            log = root / "run.log"
            log.write_text("x" * 128, encoding="utf-8")
            marker = root / "quota.marker"
            process = subprocess.Popen(["sleep", "10"], start_new_session=True)
            try:
                self.assertEqual(0, monitor.monitor(process.pid, stage, log, marker, 4096, 64, 0.1))
                process.wait(timeout=2)
                self.assertIn("quota exceeded", marker.read_text(encoding="utf-8"))
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()

    def test_short_process_completes_without_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            log = root / "run.log"
            log.write_text("", encoding="utf-8")
            marker = root / "quota.marker"
            process = subprocess.Popen(["sleep", "0.2"], start_new_session=True)
            results: list[int] = []
            worker = threading.Thread(
                target=lambda: results.append(
                    monitor.monitor(process.pid, stage, log, marker, 4096, 4096, 0.1)
                )
            )
            worker.start()
            process.wait(timeout=2)
            worker.join(timeout=2)
            self.assertFalse(worker.is_alive())
            self.assertEqual([0], results)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
