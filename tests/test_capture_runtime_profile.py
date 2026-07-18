#!/usr/bin/env python3
"""Tests for capture_runtime_profile.py."""

from __future__ import annotations

import io
import json
import re
import socket
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "wow-frontend-design" / "scripts"))

import capture_runtime_profile


class RuntimeProfileTests(unittest.TestCase):
    def _args(self, *extra: str):
        return capture_runtime_profile.parser().parse_args(
            [
                "--environment-kind",
                "ci",
                "--shell-name",
                "github-actions",
                "--node-version",
                "v22.18.0",
                "--browser-engine",
                "chromium",
                "--browser-version",
                "150.0.7871.124",
                "--font-profile-id",
                "ci-default-v1",
                "--network",
                "available",
                "--browser",
                "available",
                "--screenshots",
                "available",
                "--captured-at",
                "2026-07-16T00:00:00Z",
                *extra,
            ]
        )

    def test_profile_is_machine_readable_and_privacy_bounded(self) -> None:
        profile = capture_runtime_profile.build_profile(self._args())
        json.dumps(profile)
        self.assertEqual(profile["schema_version"], 1)
        self.assertEqual(profile["captured_at"], "2026-07-16T00:00:00Z")
        self.assertEqual(profile["captured_at_source"], "caller")
        self.assertEqual(profile["caller_declarations"]["environment_kind"], "ci")
        self.assertRegex(profile["host"]["timezone_offset"], re.compile(r"(?:[+-]\d{2}:\d{2}|not_reported)"))
        keys = set(profile) | set(profile["host"]) | set(profile["caller_declarations"]) | set(profile["capabilities"])
        for forbidden in ("hostname", "username", "home_path", "ip_address", "environment_variables"):
            self.assertNotIn(forbidden, keys)

    def test_noncanonical_timestamp_is_rejected(self) -> None:
        args = self._args()
        args.captured_at = "2026-07-16T00:00:00+00:00"
        with self.assertRaisesRegex(capture_runtime_profile.RuntimeProfileError, "canonical"):
            capture_runtime_profile.build_profile(args)

    def test_unbounded_or_whitespace_declaration_is_rejected(self) -> None:
        for value in ("bad value", "../secret", "x" * 65):
            with self.subTest(value=value):
                args = self._args()
                args.shell_name = value
                with self.assertRaisesRegex(capture_runtime_profile.RuntimeProfileError, "bounded identifier"):
                    capture_runtime_profile.build_profile(args)

    def test_main_returns_json_without_external_probe(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            result = capture_runtime_profile.main(
                ["--captured-at", "2026-07-16T00:00:00Z", "--environment-kind", "sandbox"]
            )
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(output.getvalue())["caller_declarations"]["environment_kind"], "sandbox")

    def test_profile_does_not_probe_network_commands_or_hostname(self) -> None:
        blocked = AssertionError("external probe attempted")
        with (
            mock.patch.object(socket, "socket", side_effect=blocked),
            mock.patch.object(socket, "gethostname", side_effect=blocked),
            mock.patch.object(subprocess, "run", side_effect=blocked),
            mock.patch.object(subprocess, "Popen", side_effect=blocked),
        ):
            profile = capture_runtime_profile.build_profile(self._args())
        self.assertEqual(profile["caller_declarations"]["environment_kind"], "ci")


if __name__ == "__main__":
    unittest.main()
