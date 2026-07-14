#!/usr/bin/env python3
"""Tests for evaluator-owned evidence ledger runs."""

from __future__ import annotations

import base64
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evidence_ledger


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
JPEG_1X1 = base64.b64decode(
    "/9j//gAQTGF2YzYyLjI4LjEwMgD/2wBDAAgEBAQEBAUFBQUFBQYGBgYGBgYGBgYGBgYHBwcICAgHBwcGBgcHCAgICAkJCQgICAgJCQoK"
    "CgwMCwsODg4RERT/xABNAAEBAAAAAAAAAAAAAAAAAAAABwEBAQEAAAAAAAAAAAAAAAAAAAIDEAEAAAAAAAAAAAAAAAAAAAAAEQEAAAAAAAAA"
    "AAAAAAAAAAAA/8AAEQgAAQABAwESAAISAAMSAP/aAAwDAQACEQMRAD8AtAyFD//Z"
)
JPEG_COMPONENT_MISMATCH = bytes.fromhex(
    "ffd8 ffc0000b080001000101011100 ffda0008010200003f00 01 ffd9"
)
JPEG_MISSING_TABLES = bytes.fromhex(
    "ffd8 ffc0000b080001000101011100 ffda0008010100003f00 01 ffd9"
)


class EvidenceLedgerTests(unittest.TestCase):
    def run_quietly(self, arguments: list[str]) -> int:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return evidence_ledger.main(arguments)

    def initialize(self, ledger: Path) -> None:
        self.assertEqual(
            self.run_quietly(
                [
                    "init",
                    "--ledger",
                    str(ledger),
                    "--case-id",
                    "case-001",
                    "--run-id",
                    "run-001",
                ]
            ),
            0,
        )

    def test_records_success_without_persisting_output_secret_or_absolute_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            self.initialize(ledger)
            code = self.run_quietly(
                [
                    "run",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "test",
                    "--cwd",
                    str(root),
                    "--",
                    sys.executable,
                    "-c",
                    "print('private' + chr(32) + 'output')",
                    "API_TOKEN=do-not-store",
                ]
            )

            self.assertEqual(code, 0)
            value = json.loads(ledger.read_text(encoding="utf-8"))
            event = value["events"][0]
            self.assertEqual(event["exit_code"], 0)
            self.assertEqual(event["cwd"], ".")
            self.assertGreater(event["stdout_bytes"], 0)
            self.assertNotIn("private output", ledger.read_text(encoding="utf-8"))
            self.assertNotIn(str(root), ledger.read_text(encoding="utf-8"))
            self.assertIn("API_TOKEN=[REDACTED]", event["command"])

    def test_latest_failed_label_fails_check(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            self.initialize(ledger)
            code = self.run_quietly(
                [
                    "run",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "build",
                    "--cwd",
                    str(root),
                    "--",
                    sys.executable,
                    "-c",
                    "raise SystemExit(3)",
                ]
            )
            self.assertEqual(code, 3)
            self.assertEqual(
                self.run_quietly(["check", "--ledger", str(ledger), "--require-label", "build"]),
                1,
            )

    def test_screenshot_requires_real_image_and_structured_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            screenshot = root / "mobile.png"
            screenshot.write_bytes(PNG_1X1)
            self.initialize(ledger)

            self.assertEqual(
                self.run_quietly(
                    [
                        "artifact",
                        "--ledger",
                        str(ledger),
                        "--label",
                        "mobile-390",
                        "--kind",
                        "screenshot",
                        "--path",
                        str(screenshot),
                        "--route",
                        "/",
                        "--viewport",
                        "390x844",
                        "--locale",
                        "zh-Hant-TW",
                        "--state",
                        "default",
                    ]
                ),
                0,
            )
            value = json.loads(ledger.read_text(encoding="utf-8"))
            event = value["events"][-1]
            self.assertEqual(event["media_type"], "image/png")
            self.assertEqual((event["width"], event["height"]), (1, 1))
            self.assertEqual(event["path"], "mobile.png")

    def test_valid_jpeg_structure_still_requires_a_real_decoder(self) -> None:
        self.assertEqual(evidence_ledger.jpeg_structure_metadata(JPEG_1X1), (1, 1))
        with mock.patch.object(evidence_ledger, "load_pillow_image_module", return_value=None):
            with self.assertRaisesRegex(evidence_ledger.LedgerError, "marker validation alone"):
                evidence_ledger.screenshot_metadata(JPEG_1X1)

    def test_jpeg_artifact_is_not_recorded_without_a_real_decoder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            screenshot = root / "mobile.jpg"
            screenshot.write_bytes(JPEG_1X1)
            self.initialize(ledger)

            with mock.patch.object(evidence_ledger, "load_pillow_image_module", return_value=None):
                code = self.run_quietly(
                    [
                        "artifact",
                        "--ledger",
                        str(ledger),
                        "--label",
                        "mobile-jpeg",
                        "--kind",
                        "screenshot",
                        "--path",
                        str(screenshot),
                        "--route",
                        "/",
                        "--viewport",
                        "390x844",
                        "--state",
                        "default",
                    ]
                )

            self.assertEqual(code, 2)
            self.assertEqual(json.loads(ledger.read_text(encoding="utf-8"))["events"], [])

    def test_valid_jpeg_fully_loads_when_pillow_is_available(self) -> None:
        if evidence_ledger.load_pillow_image_module() is None:
            self.skipTest("optional evaluator-owned Pillow decoder is unavailable")
        self.assertEqual(evidence_ledger.screenshot_metadata(JPEG_1X1), ("image/jpeg", 1, 1))

    def test_jpeg_scan_cannot_reference_an_undeclared_component(self) -> None:
        with self.assertRaisesRegex(evidence_ledger.LedgerError, "invalid frame component"):
            evidence_ledger.screenshot_metadata(JPEG_COMPONENT_MISMATCH)

    def test_jpeg_scan_cannot_use_missing_quantization_table(self) -> None:
        with self.assertRaisesRegex(evidence_ledger.LedgerError, "missing quantization table"):
            evidence_ledger.screenshot_metadata(JPEG_MISSING_TABLES)

    def test_jpeg_scan_cannot_use_missing_huffman_table(self) -> None:
        table_marker = JPEG_1X1.find(b"\xff\xc4")
        self.assertGreaterEqual(table_marker, 0)
        table_length = int.from_bytes(JPEG_1X1[table_marker + 2 : table_marker + 4], "big")
        without_huffman_tables = (
            JPEG_1X1[:table_marker] + JPEG_1X1[table_marker + 2 + table_length :]
        )

        with self.assertRaisesRegex(evidence_ledger.LedgerError, "missing Huffman table"):
            evidence_ledger.screenshot_metadata(without_huffman_tables)

    def test_jpeg_verify_without_full_pixel_load_is_rejected(self) -> None:
        class FakeImage:
            format = "JPEG"
            size = (1, 1)

            def __init__(self, fail_load: bool) -> None:
                self.fail_load = fail_load

            def __enter__(self) -> "FakeImage":
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def verify(self) -> None:
                return None

            def load(self) -> None:
                if self.fail_load:
                    raise OSError("corrupt entropy stream")

        class FakeImageModule:
            DecompressionBombWarning = UserWarning

            def __init__(self) -> None:
                self.opens = 0

            def open(self, _: object) -> FakeImage:
                self.opens += 1
                return FakeImage(fail_load=self.opens == 2)

        with mock.patch.object(
            evidence_ledger,
            "load_pillow_image_module",
            return_value=FakeImageModule(),
        ):
            with self.assertRaisesRegex(evidence_ledger.LedgerError, "could not fully load"):
                evidence_ledger.screenshot_metadata(JPEG_1X1)

    def test_truncated_and_corrupt_jpeg_are_rejected_before_decode(self) -> None:
        corrupt_table = bytearray(JPEG_1X1)
        table_marker = corrupt_table.find(b"\xff\xdb")
        self.assertGreaterEqual(table_marker, 0)
        corrupt_table[table_marker + 4] = 0xF0

        hostile = (
            (JPEG_1X1[:-2], "missing a following marker|missing frame, scan, or EOI"),
            (bytes(corrupt_table), "quantization table is invalid"),
        )
        for content, message in hostile:
            with self.subTest(message=message), self.assertRaisesRegex(evidence_ledger.LedgerError, message):
                evidence_ledger.screenshot_metadata(content)

    def test_fake_screenshot_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            screenshot = root / "mobile.png"
            screenshot.write_bytes(b"not-a-real-png")
            self.initialize(ledger)

            code = self.run_quietly(
                [
                    "artifact",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "mobile-390",
                    "--kind",
                    "screenshot",
                    "--path",
                    str(screenshot),
                    "--route",
                    "/",
                    "--viewport",
                    "390x844",
                    "--state",
                    "default",
                ]
            )

            self.assertEqual(code, 2)

    def test_png_header_without_decodable_chunks_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            screenshot = root / "header-only.png"
            screenshot.write_bytes(PNG_1X1[:24])
            self.initialize(ledger)

            code = self.run_quietly(
                [
                    "artifact",
                    "--ledger",
                    str(ledger),
                    "--label",
                    "header-only",
                    "--kind",
                    "screenshot",
                    "--path",
                    str(screenshot),
                    "--route",
                    "/",
                    "--viewport",
                    "390x844",
                    "--state",
                    "default",
                ]
            )

            self.assertEqual(code, 2)

    def test_tampered_command_hash_or_run_id_invalidates_ledger(self) -> None:
        for field, replacement in (("command", ["false"]), ("run_id", "other-run")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                ledger = root / "evidence.json"
                self.initialize(ledger)
                self.assertEqual(
                    self.run_quietly(
                        [
                            "run",
                            "--ledger",
                            str(ledger),
                            "--label",
                            "syntax",
                            "--cwd",
                            str(root),
                            "--",
                            sys.executable,
                            "-c",
                            "pass",
                        ]
                    ),
                    0,
                )
                value = json.loads(ledger.read_text(encoding="utf-8"))
                value["events"][0][field] = replacement
                ledger.write_text(json.dumps(value), encoding="utf-8")

                self.assertEqual(self.run_quietly(["summary", "--ledger", str(ledger)]), 2)

    def test_nonempty_labels_must_be_trimmed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            self.initialize(ledger)

            self.assertEqual(
                self.run_quietly(
                    [
                        "run",
                        "--ledger",
                        str(ledger),
                        "--label",
                        " syntax ",
                        "--cwd",
                        str(root),
                        "--",
                        sys.executable,
                        "-c",
                        "pass",
                    ]
                ),
                2,
            )

    def test_latest_missing_artifact_overrides_old_present_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            report = root / "report.json"
            report.write_text("{}", encoding="utf-8")
            self.initialize(ledger)
            base = [
                "artifact",
                "--ledger",
                str(ledger),
                "--label",
                "report",
                "--kind",
                "report",
                "--path",
                str(report),
            ]
            self.assertEqual(self.run_quietly(base), 0)
            report.unlink()
            self.assertEqual(self.run_quietly(base), 1)
            self.assertEqual(
                self.run_quietly(
                    ["check", "--ledger", str(ledger), "--require-artifact", "report"]
                ),
                1,
            )

    def test_changed_artifact_fails_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = root / "evidence.json"
            report = root / "report.json"
            report.write_text("{}", encoding="utf-8")
            self.initialize(ledger)
            record = [
                "artifact",
                "--ledger",
                str(ledger),
                "--label",
                "report",
                "--kind",
                "report",
                "--path",
                str(report),
            ]
            self.assertEqual(self.run_quietly(record), 0)
            report.write_text('{"changed":true}', encoding="utf-8")

            self.assertEqual(
                self.run_quietly(
                    ["check", "--ledger", str(ledger), "--require-artifact", "report"]
                ),
                1,
            )

    def test_rejects_symlink_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target.json"
            target.write_text(json.dumps(evidence_ledger.empty_ledger()), encoding="utf-8")
            link = root / "evidence.json"
            link.symlink_to(target)

            self.assertEqual(self.run_quietly(["summary", "--ledger", str(link)]), 2)


if __name__ == "__main__":
    unittest.main()
