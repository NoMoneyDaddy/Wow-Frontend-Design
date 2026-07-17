#!/usr/bin/env python3
"""Tests for validate_external_sources.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_external_sources


class SourceLockTests(unittest.TestCase):
    def test_repository_lock_is_valid(self) -> None:
        root = Path(__file__).resolve().parents[2]
        count = validate_external_sources.validate(
            root / "wow-frontend-design" / "references" / "external-sources.lock.json"
        )
        self.assertEqual(count, 65)

    def test_short_revision_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lock.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "retrieved_at": "2026-07-14",
                        "policy": "Pinned research only; verify before any use.",
                        "sources": [
                            {
                                "repository": "example/repo",
                                "revision": "deadbeef",
                                "license": "MIT",
                                "paths": ["SKILL.md"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validate_external_sources.SourceLockError):
                validate_external_sources.validate(path)

    def test_oversized_and_deep_locks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (validate_external_sources.MAX_LOCK_BYTES + 1))
            with self.assertRaisesRegex(validate_external_sources.SourceLockError, "exceeds"):
                validate_external_sources.load(oversized)

            deep = root / "deep.json"
            deep.write_text("[" * 1_100 + "]" * 1_100, encoding="utf-8")
            with self.assertRaises(validate_external_sources.SourceLockError):
                validate_external_sources.load(deep)


if __name__ == "__main__":
    unittest.main()
