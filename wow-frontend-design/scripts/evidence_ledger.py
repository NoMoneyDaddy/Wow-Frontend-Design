#!/usr/bin/env python3
"""Record command and artifact facts so agents do not rely on self-reported passes."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import time
import warnings
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 3
MAX_SCREENSHOT_BYTES = 50_000_000
MAX_DECODED_SCREENSHOT_BYTES = 100_000_000
MAX_IMAGE_DIMENSION = 32_768
MAX_IMAGE_PIXELS = 100_000_000
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
LEDGER_TRUST_BOUNDARY = {
    "integrity": "unsigned",
    "requirement": "evaluator-owned ledger and policy must remain outside the model-writable workspace",
}
SENSITIVE_FLAGS = {
    "--api-key",
    "--authorization",
    "--cookie",
    "--header",
    "--key",
    "--password",
    "--proxy-user",
    "--secret",
    "--token",
    "--user",
    "-H",
    "-p",
    "-u",
}
SENSITIVE_ASSIGNMENTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "secret",
    "session",
    "token",
)
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class LedgerError(ValueError):
    """Raised when a ledger is malformed or unsafe to update."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_command_sha256(command: list[str]) -> str:
    return sha256_bytes(json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def require_trimmed_string(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise LedgerError(f"{field} must be a string")
    if value != value.strip():
        raise LedgerError(f"{field} must not have leading or trailing whitespace")
    if not allow_empty and not value:
        raise LedgerError(f"{field} must be non-empty")
    return value


def require_nonnegative_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LedgerError(f"{field} must be a non-negative integer")
    return value


def require_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
        raise LedgerError(f"{field} must be a lowercase SHA-256 digest")
    return value


def require_timestamp(value: Any, field: str) -> str:
    text = require_trimmed_string(value, field)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise LedgerError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LedgerError(f"{field} must include a timezone")
    return text


def require_relative_path(value: Any, field: str) -> str:
    text = require_trimmed_string(value, field)
    candidate = Path(text)
    if candidate.is_absolute() or ".." in candidate.parts or text.startswith(("/", "\\")):
        raise LedgerError(f"{field} must be a safe relative path")
    return text


def emit_bytes(stream: Any, value: bytes) -> None:
    if not value:
        return
    binary = getattr(stream, "buffer", None)
    if binary is not None:
        binary.write(value)
    else:
        stream.write(value.decode("utf-8", errors="replace"))


def redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    hide_next = False
    for argument in command:
        if hide_next:
            redacted.append("[REDACTED]")
            hide_next = False
            continue

        lowered = argument.lower()
        if lowered in SENSITIVE_FLAGS:
            redacted.append(argument)
            hide_next = True
            continue

        if "=" in argument:
            key, _ = argument.split("=", 1)
            if any(marker in key.lower() for marker in SENSITIVE_ASSIGNMENTS):
                redacted.append(f"{key}=[REDACTED]")
                continue

        redacted.append(re.sub(r"(://[^:/\s]+:)[^@/\s]+@", r"\1[REDACTED]@", argument))
    return redacted


def empty_ledger(case_id: str = "test-case", run_id: str = "test-run") -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "run_id": run_id,
        "root": ".",
        "trust_boundary": dict(LEDGER_TRUST_BOUNDARY),
        "events": [],
    }


def validate_event(event: Any, expected_run_id: str, index: int | str = "?") -> dict[str, Any]:
    label = f"events[{index}]"
    if not isinstance(event, dict):
        raise LedgerError(f"{label} must be an object")
    kind = event.get("kind")
    common = {"kind", "label", "run_id", "recorded_at"}
    if kind == "command":
        required = common | {
            "started_at",
            "cwd",
            "command",
            "command_sha256",
            "exit_code",
            "duration_ms",
            "stdout_bytes",
            "stdout_sha256",
            "stderr_bytes",
            "stderr_sha256",
        }
        allowed = required | {"execution_error"}
    elif kind == "artifact":
        required = common | {"artifact_kind", "path", "exists"}
        allowed = required | {"bytes", "sha256", "media_type", "width", "height", "context"}
    else:
        raise LedgerError(f"{label}.kind must be command or artifact")
    missing = required - set(event)
    extra = set(event) - allowed
    if missing:
        raise LedgerError(f"{label} is missing fields: {sorted(missing)}")
    if extra:
        raise LedgerError(f"{label} has unexpected fields: {sorted(extra)}")

    require_trimmed_string(event["label"], f"{label}.label")
    run_id = require_trimmed_string(event["run_id"], f"{label}.run_id")
    if RUN_ID_PATTERN.fullmatch(run_id) is None or run_id != expected_run_id:
        raise LedgerError(f"{label}.run_id does not match the ledger run_id")
    require_timestamp(event["recorded_at"], f"{label}.recorded_at")

    if kind == "command":
        require_timestamp(event["started_at"], f"{label}.started_at")
        require_relative_path(event["cwd"], f"{label}.cwd")
        command = event["command"]
        if not isinstance(command, list) or not command:
            raise LedgerError(f"{label}.command must be a non-empty string list")
        for command_index, argument in enumerate(command):
            require_trimmed_string(argument, f"{label}.command[{command_index}]", allow_empty=True)
        digest = require_sha256(event["command_sha256"], f"{label}.command_sha256")
        if digest != canonical_command_sha256(command):
            raise LedgerError(f"{label}.command_sha256 does not match command")
        if not isinstance(event["exit_code"], int) or isinstance(event["exit_code"], bool):
            raise LedgerError(f"{label}.exit_code must be an integer")
        for field in ("duration_ms", "stdout_bytes", "stderr_bytes"):
            require_nonnegative_int(event[field], f"{label}.{field}")
        require_sha256(event["stdout_sha256"], f"{label}.stdout_sha256")
        require_sha256(event["stderr_sha256"], f"{label}.stderr_sha256")
        if "execution_error" in event:
            require_trimmed_string(event["execution_error"], f"{label}.execution_error")
        return event

    if event["artifact_kind"] not in {"screenshot", "report", "trace", "other"}:
        raise LedgerError(f"{label}.artifact_kind is invalid")
    require_relative_path(event["path"], f"{label}.path")
    if not isinstance(event["exists"], bool):
        raise LedgerError(f"{label}.exists must be boolean")
    context = event.get("context")
    if context is not None:
        if not isinstance(context, dict) or set(context) - {"route", "viewport", "locale", "state", "note"}:
            raise LedgerError(f"{label}.context is invalid")
        for key, value in context.items():
            require_trimmed_string(value, f"{label}.context.{key}")
    if event["exists"] is True:
        for field in ("bytes", "sha256"):
            if field not in event:
                raise LedgerError(f"{label}.{field} is required for a present artifact")
        require_nonnegative_int(event["bytes"], f"{label}.bytes")
        require_sha256(event["sha256"], f"{label}.sha256")
        if event["artifact_kind"] == "screenshot":
            for field in ("media_type", "width", "height"):
                if field not in event:
                    raise LedgerError(f"{label}.{field} is required for a screenshot")
            if event["media_type"] not in {"image/png", "image/jpeg"}:
                raise LedgerError(f"{label}.media_type must be image/png or image/jpeg")
            if not all(
                isinstance(event.get(field), int) and not isinstance(event[field], bool) and event[field] > 0
                for field in ("width", "height")
            ):
                raise LedgerError(f"{label} screenshot dimensions must be positive integers")
            if not isinstance(context, dict) or not all(context.get(key) for key in ("route", "viewport", "state")):
                raise LedgerError(f"{label} screenshot requires route, viewport, and state context")
        elif set(event) & {"media_type", "width", "height"}:
            raise LedgerError(f"{label} non-screenshot artifact must not contain image metadata")
    elif set(event) & {"bytes", "sha256", "media_type", "width", "height"}:
        raise LedgerError(f"{label} missing artifact must not contain content metadata")
    return event


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise LedgerError("ledger is not initialized; run the init action first")
    if path.is_symlink():
        raise LedgerError("refusing to update a symlink ledger")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LedgerError(f"cannot read ledger: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise LedgerError("unsupported or missing ledger schema_version")
    expected_keys = {"schema_version", "case_id", "run_id", "root", "trust_boundary", "events"}
    if set(value) != expected_keys:
        raise LedgerError("ledger root has missing or unexpected fields")
    if not isinstance(value.get("case_id"), str) or not value["case_id"].strip():
        raise LedgerError("ledger case_id must be a non-empty string")
    if value["case_id"] != value["case_id"].strip():
        raise LedgerError("ledger case_id must be trimmed")
    if not isinstance(value.get("run_id"), str) or RUN_ID_PATTERN.fullmatch(value["run_id"]) is None:
        raise LedgerError("ledger run_id is missing or invalid")
    if value.get("root") != ".":
        raise LedgerError("ledger root must remain project-relative '.'")
    if value.get("trust_boundary") != LEDGER_TRUST_BOUNDARY:
        raise LedgerError("ledger must declare its unsigned evaluator-owned trust boundary")
    if not isinstance(value.get("events"), list):
        raise LedgerError("ledger events must be a list")
    for index, event in enumerate(value["events"]):
        validate_event(event, value["run_id"], index)
    return value


def save_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise LedgerError("refusing to replace a symlink ledger")
    payload = json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def append_event(path: Path, event: dict[str, Any]) -> None:
    ledger = load_ledger(path)
    validate_event(event, ledger["run_id"], len(ledger["events"]))
    ledger["events"].append(event)
    save_ledger(path, ledger)


def init_ledger(args: argparse.Namespace) -> int:
    path = Path(args.ledger).expanduser()
    if path.exists():
        raise LedgerError("refusing to overwrite an existing ledger")
    if not args.case_id.strip():
        raise LedgerError("case-id must be non-empty")
    if args.run_id != args.run_id.strip() or RUN_ID_PATTERN.fullmatch(args.run_id) is None:
        raise LedgerError("run-id must match [A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise LedgerError("refusing a ledger inside a symlink directory")
    save_ledger(path, empty_ledger(args.case_id.strip(), args.run_id))
    return 0


def relative_to_ledger_root(ledger_path: Path, candidate: Path, purpose: str) -> tuple[Path, str]:
    root = ledger_path.expanduser().resolve().parent
    resolved = candidate.expanduser().resolve()
    try:
        rel = resolved.relative_to(root).as_posix()
    except ValueError as error:
        raise LedgerError(f"{purpose} must stay inside the ledger project root") from error
    return resolved, rel or "."


def validate_image_dimensions(width: int, height: int) -> None:
    if width <= 0 or height <= 0:
        raise LedgerError("screenshot dimensions must be non-zero")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise LedgerError(f"screenshot dimension exceeds {MAX_IMAGE_DIMENSION}px")
    if width * height > MAX_IMAGE_PIXELS:
        raise LedgerError(f"screenshot exceeds {MAX_IMAGE_PIXELS} pixels")


def png_passes(width: int, height: int, interlace: int) -> list[tuple[int, int]]:
    if interlace == 0:
        return [(width, height)]
    passes: list[tuple[int, int]] = []
    for start_x, start_y, step_x, step_y in (
        (0, 0, 8, 8),
        (4, 0, 8, 8),
        (0, 4, 4, 8),
        (2, 0, 4, 4),
        (0, 2, 2, 4),
        (1, 0, 2, 2),
        (0, 1, 1, 2),
    ):
        pass_width = 0 if width <= start_x else (width - start_x + step_x - 1) // step_x
        pass_height = 0 if height <= start_y else (height - start_y + step_y - 1) // step_y
        if pass_width and pass_height:
            passes.append((pass_width, pass_height))
    return passes


def png_metadata(content: bytes) -> tuple[str, int, int]:
    signature = b"\x89PNG\r\n\x1a\n"
    if not content.startswith(signature):
        raise LedgerError("PNG signature is invalid")
    offset = len(signature)
    width = height = bit_depth = color_type = interlace = 0
    seen_ihdr = seen_idat = seen_iend = seen_plte = False
    idat_ended = False
    idat = bytearray()
    while offset < len(content):
        if offset + 12 > len(content):
            raise LedgerError("PNG chunk header is truncated")
        length = struct.unpack(">I", content[offset : offset + 4])[0]
        chunk_type = content[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(content):
            raise LedgerError("PNG chunk is truncated")
        if len(chunk_type) != 4 or not all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in chunk_type):
            raise LedgerError("PNG chunk type is invalid")
        expected_crc = struct.unpack(">I", content[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + content[data_start:data_end]) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise LedgerError(f"PNG {chunk_type.decode('ascii', errors='replace')} CRC is invalid")
        if not seen_ihdr and chunk_type != b"IHDR":
            raise LedgerError("PNG IHDR must be the first chunk")
        if chunk_type == b"IHDR":
            if seen_ihdr or length != 13:
                raise LedgerError("PNG must contain one 13-byte IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", content[data_start:data_end]
            )
            validate_image_dimensions(width, height)
            allowed_depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
            if color_type not in allowed_depths or bit_depth not in allowed_depths[color_type]:
                raise LedgerError("PNG color type/bit depth combination is unsupported")
            if compression != 0 or filtering != 0 or interlace not in {0, 1}:
                raise LedgerError("PNG compression, filter, or interlace method is invalid")
            seen_ihdr = True
        elif chunk_type == b"PLTE":
            if seen_idat or length == 0 or length % 3 or length > 768:
                raise LedgerError("PNG palette is invalid")
            seen_plte = True
        elif chunk_type == b"IDAT":
            if idat_ended:
                raise LedgerError("PNG IDAT chunks must be consecutive")
            seen_idat = True
            idat.extend(content[data_start:data_end])
        elif chunk_type == b"IEND":
            if length != 0 or not seen_idat:
                raise LedgerError("PNG IEND is invalid or image data is missing")
            seen_iend = True
            offset = crc_end
            if offset != len(content):
                raise LedgerError("PNG contains trailing bytes after IEND")
            break
        else:
            if seen_idat:
                idat_ended = True
            if chunk_type[0] & 0x20 == 0:
                raise LedgerError(f"PNG contains unknown critical chunk {chunk_type!r}")
        offset = crc_end
    if not (seen_ihdr and seen_idat and seen_iend):
        raise LedgerError("PNG is missing IHDR, IDAT, or IEND")
    if color_type == 3 and not seen_plte:
        raise LedgerError("indexed PNG is missing PLTE")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bits_per_pixel = channels * bit_depth
    pass_layout: list[tuple[int, int]] = []
    expected_bytes = 0
    for pass_width, pass_height in png_passes(width, height, interlace):
        row_bytes = (pass_width * bits_per_pixel + 7) // 8
        pass_layout.append((row_bytes, pass_height))
        expected_bytes += pass_height * (row_bytes + 1)
    if expected_bytes > MAX_DECODED_SCREENSHOT_BYTES:
        raise LedgerError(f"PNG decoded data exceeds {MAX_DECODED_SCREENSHOT_BYTES} bytes")
    try:
        decompressor = zlib.decompressobj()
        decoded = decompressor.decompress(bytes(idat), expected_bytes + 1)
        decoded += decompressor.flush(max(expected_bytes + 1 - len(decoded), 1))
    except zlib.error as error:
        raise LedgerError(f"PNG image data cannot be decompressed: {error}") from error
    if len(decoded) != expected_bytes or not decompressor.eof or decompressor.unused_data or decompressor.unconsumed_tail:
        raise LedgerError("PNG decompressed scanline length is invalid")
    decoded_offset = 0
    for row_bytes, pass_height in pass_layout:
        for _ in range(pass_height):
            if decoded[decoded_offset] > 4:
                raise LedgerError("PNG scanline uses an invalid filter")
            decoded_offset += row_bytes + 1
    return "image/png", width, height


def parse_jpeg_quantization_tables(segment: bytes, tables: set[int]) -> None:
    offset = 0
    while offset < len(segment):
        table_info = segment[offset]
        offset += 1
        precision = table_info >> 4
        table_id = table_info & 0x0F
        if precision not in {0, 1} or table_id > 3:
            raise LedgerError("JPEG quantization table is invalid")
        table_bytes = 64 * (precision + 1)
        if offset + table_bytes > len(segment):
            raise LedgerError("JPEG quantization table is truncated")
        table = segment[offset : offset + table_bytes]
        if precision == 0:
            has_zero_value = 0 in table
        else:
            has_zero_value = any(
                table[index : index + 2] == b"\x00\x00"
                for index in range(0, len(table), 2)
            )
        if has_zero_value:
            raise LedgerError("JPEG quantization table contains a zero value")
        offset += table_bytes
        tables.add(table_id)
    if offset != len(segment):
        raise LedgerError("JPEG quantization table segment is invalid")


def parse_jpeg_huffman_tables(segment: bytes, tables: set[tuple[int, int]]) -> None:
    offset = 0
    while offset < len(segment):
        table_info = segment[offset]
        offset += 1
        table_class = table_info >> 4
        table_id = table_info & 0x0F
        if table_class not in {0, 1} or table_id > 3 or offset + 16 > len(segment):
            raise LedgerError("JPEG Huffman table is invalid or truncated")
        counts = segment[offset : offset + 16]
        offset += 16
        symbol_count = sum(counts)
        if symbol_count == 0 or symbol_count > 256 or offset + symbol_count > len(segment):
            raise LedgerError("JPEG Huffman table symbols are invalid or truncated")
        remaining_codes = 1
        for count in counts:
            remaining_codes = remaining_codes * 2 - count
            if remaining_codes < 0:
                raise LedgerError("JPEG Huffman table is oversubscribed")
        offset += symbol_count
        tables.add((table_class, table_id))
    if offset != len(segment):
        raise LedgerError("JPEG Huffman table segment is invalid")


def jpeg_structure_metadata(content: bytes) -> tuple[int, int]:
    """Validate bounded JPEG structure before handing bytes to a real decoder."""
    if not content.startswith(b"\xff\xd8"):
        raise LedgerError("JPEG SOI marker is missing")
    offset = 2
    width = height = 0
    seen_sof = seen_sos = seen_eoi = False
    frame_marker = 0
    frame_components: dict[int, int] = {}
    quantization_tables: set[int] = set()
    huffman_tables: set[tuple[int, int]] = set()
    while offset < len(content):
        if content[offset] != 0xFF:
            raise LedgerError("JPEG marker boundary is invalid")
        while offset < len(content) and content[offset] == 0xFF:
            offset += 1
        if offset >= len(content):
            raise LedgerError("JPEG marker is truncated")
        marker = content[offset]
        offset += 1
        if marker == 0xD9:
            seen_eoi = True
            if offset != len(content):
                raise LedgerError("JPEG contains trailing bytes after EOI")
            break
        if marker in {0x00, 0x01, 0xD8} or 0xD0 <= marker <= 0xD7:
            raise LedgerError(f"JPEG marker 0x{marker:02x} is invalid outside scan data")
        if offset + 2 > len(content):
            raise LedgerError("JPEG segment length is truncated")
        length = int.from_bytes(content[offset : offset + 2], "big")
        if length < 2 or offset + length > len(content):
            raise LedgerError("JPEG segment length is invalid")
        data_start = offset + 2
        data_end = offset + length
        segment = content[data_start:data_end]
        if marker == 0xDB:
            parse_jpeg_quantization_tables(segment, quantization_tables)
        elif marker == 0xC4:
            parse_jpeg_huffman_tables(segment, huffman_tables)
        elif marker in {0xC0, 0xC2}:
            if seen_sof or length < 11:
                raise LedgerError("JPEG frame header is invalid")
            precision = segment[0]
            height = int.from_bytes(segment[1:3], "big")
            width = int.from_bytes(segment[3:5], "big")
            components = segment[5]
            if precision != 8 or components not in {1, 3, 4} or length != 8 + 3 * components:
                raise LedgerError("JPEG frame precision or components are invalid")
            validate_image_dimensions(width, height)
            if width * height * components > MAX_DECODED_SCREENSHOT_BYTES:
                raise LedgerError(f"JPEG decoded data exceeds {MAX_DECODED_SCREENSHOT_BYTES} bytes")
            for component_index in range(components):
                component_offset = 6 + component_index * 3
                component_id = segment[component_offset]
                sampling = segment[component_offset + 1]
                table_id = segment[component_offset + 2]
                horizontal_sampling = sampling >> 4
                vertical_sampling = sampling & 0x0F
                if (
                    component_id == 0
                    or component_id in frame_components
                    or horizontal_sampling not in {1, 2, 3, 4}
                    or vertical_sampling not in {1, 2, 3, 4}
                    or table_id > 3
                ):
                    raise LedgerError("JPEG frame component descriptor is invalid")
                frame_components[component_id] = table_id
            frame_marker = marker
            seen_sof = True
        elif marker in {0xC1, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            raise LedgerError("JPEG frame type is unsupported for screenshot evidence")
        elif marker == 0xDD and length != 4:
            raise LedgerError("JPEG restart interval segment is invalid")
        offset = data_end
        if marker != 0xDA:
            continue
        if not seen_sof:
            raise LedgerError("JPEG scan appears before frame header")
        if length < 8:
            raise LedgerError("JPEG scan header is invalid")
        scan_components = segment[0]
        if scan_components < 1 or scan_components > len(frame_components) or length != 6 + 2 * scan_components:
            raise LedgerError("JPEG scan component count is invalid")
        selected_components: list[tuple[int, int, int]] = []
        seen_component_ids: set[int] = set()
        for scan_index in range(scan_components):
            scan_offset = 1 + scan_index * 2
            component_id = segment[scan_offset]
            table_selectors = segment[scan_offset + 1]
            dc_table = table_selectors >> 4
            ac_table = table_selectors & 0x0F
            if component_id not in frame_components or component_id in seen_component_ids or dc_table > 3 or ac_table > 3:
                raise LedgerError("JPEG scan references an invalid frame component or Huffman table")
            if frame_components[component_id] not in quantization_tables:
                raise LedgerError("JPEG scan references a missing quantization table")
            selected_components.append((component_id, dc_table, ac_table))
            seen_component_ids.add(component_id)
        spectral_start, spectral_end, approximation = segment[-3:]
        approximation_high = approximation >> 4
        approximation_low = approximation & 0x0F
        if frame_marker == 0xC0:
            if (spectral_start, spectral_end, approximation) != (0, 63, 0):
                raise LedgerError("baseline JPEG scan parameters are invalid")
            for _, dc_table, ac_table in selected_components:
                if (0, dc_table) not in huffman_tables or (1, ac_table) not in huffman_tables:
                    raise LedgerError("baseline JPEG scan references a missing Huffman table")
        else:
            if approximation_high > 13 or approximation_low > 13:
                raise LedgerError("progressive JPEG approximation is invalid")
            if spectral_start == 0:
                if spectral_end != 0:
                    raise LedgerError("progressive JPEG DC scan range is invalid")
                for _, dc_table, _ in selected_components:
                    if (0, dc_table) not in huffman_tables:
                        raise LedgerError("progressive JPEG DC scan references a missing Huffman table")
            else:
                if scan_components != 1 or not (1 <= spectral_start <= spectral_end <= 63):
                    raise LedgerError("progressive JPEG AC scan range is invalid")
                if (1, selected_components[0][2]) not in huffman_tables:
                    raise LedgerError("progressive JPEG AC scan references a missing Huffman table")
        seen_sos = True
        entropy_found = False
        while offset < len(content):
            marker_pos = content.find(b"\xff", offset)
            if marker_pos < 0 or marker_pos + 1 >= len(content):
                raise LedgerError("JPEG scan is missing a following marker")
            if marker_pos > offset:
                entropy_found = True
            next_byte = content[marker_pos + 1]
            if next_byte == 0x00:
                entropy_found = True
                offset = marker_pos + 2
                continue
            if next_byte == 0xFF:
                offset = marker_pos + 1
                continue
            if 0xD0 <= next_byte <= 0xD7:
                offset = marker_pos + 2
                continue
            offset = marker_pos
            break
        if not entropy_found:
            raise LedgerError("JPEG scan contains no entropy-coded data")
    if not (seen_sof and seen_sos and seen_eoi):
        raise LedgerError("JPEG is missing frame, scan, or EOI data")
    return width, height


def load_pillow_image_module() -> Any | None:
    """Load an optional evaluator-owned JPEG decoder without making it a dependency."""
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except (ImportError, OSError):
        return None
    return Image


def jpeg_metadata(content: bytes) -> tuple[str, int, int]:
    width, height = jpeg_structure_metadata(content)
    image_module = load_pillow_image_module()
    if image_module is None:
        raise LedgerError(
            "JPEG screenshot rejected: an evaluator-owned Pillow decoder is unavailable; "
            "marker validation alone is not full decoding"
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", image_module.DecompressionBombWarning)
            with image_module.open(io.BytesIO(content)) as image:
                if image.format != "JPEG" or image.size != (width, height):
                    raise LedgerError("JPEG decoder metadata does not match validated structure")
                image.verify()
            with image_module.open(io.BytesIO(content)) as image:
                if image.format != "JPEG" or image.size != (width, height):
                    raise LedgerError("JPEG decoder metadata changed between verification and load")
                image.load()
    except LedgerError:
        raise
    except Exception as error:
        raise LedgerError(f"JPEG decoder rejected or could not fully load the image: {error}") from error
    return "image/jpeg", width, height


def screenshot_metadata(content: bytes) -> tuple[str, int, int]:
    if not content or len(content) > MAX_SCREENSHOT_BYTES:
        raise LedgerError(f"screenshot must be between 1 and {MAX_SCREENSHOT_BYTES} bytes")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return png_metadata(content)
    if content.startswith(b"\xff\xd8"):
        return jpeg_metadata(content)
    raise LedgerError("screenshot must be a fully decoded PNG or JPEG")


def verify_artifact_event(event: dict[str, Any], evidence_root: Path) -> str | None:
    try:
        relative_path = require_relative_path(event.get("path"), "artifact.path")
        root = evidence_root.expanduser().resolve()
        candidate = root / relative_path
        if candidate.is_symlink():
            return "artifact path is a symlink"
        resolved = candidate.resolve()
        resolved.relative_to(root)
        if not resolved.is_file():
            return "artifact file is missing"
        content = resolved.read_bytes()
        if event.get("bytes") != len(content):
            return "artifact byte count no longer matches ledger"
        if event.get("sha256") != sha256_bytes(content):
            return "artifact SHA-256 no longer matches ledger"
        if event.get("artifact_kind") == "screenshot":
            try:
                media_type, width, height = screenshot_metadata(content)
            except LedgerError as error:
                return f"screenshot full-decode validation failed: {error}"
            if (event.get("media_type"), event.get("width"), event.get("height")) != (
                media_type,
                width,
                height,
            ):
                return "screenshot media type or dimensions no longer match ledger"
    except (LedgerError, OSError, ValueError) as error:
        return f"artifact cannot be revalidated: {error}"
    return None


def run_command(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise LedgerError("run requires a command after --")
    label = require_trimmed_string(args.label, "label")
    for index, argument in enumerate(command):
        require_trimmed_string(argument, f"command[{index}]", allow_empty=True)

    ledger_path = Path(args.ledger).expanduser()
    ledger = load_ledger(ledger_path)
    cwd, cwd_relative = relative_to_ledger_root(ledger_path, Path(args.cwd), "working directory")
    if not cwd.is_dir():
        raise LedgerError(f"working directory does not exist: {cwd}")

    started_at = now_iso()
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, capture_output=True, check=False)
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        execution_error = None
    except FileNotFoundError as error:
        exit_code = 127
        stdout = b""
        stderr = str(error).encode("utf-8", errors="replace")
        execution_error = "command not found"
    except OSError as error:
        exit_code = 126
        stdout = b""
        stderr = str(error).encode("utf-8", errors="replace")
        execution_error = "command could not execute"

    duration_ms = round((time.monotonic() - started) * 1000)
    event = {
        "kind": "command",
        "label": label,
        "recorded_at": now_iso(),
        "started_at": started_at,
        "run_id": ledger["run_id"],
        "cwd": cwd_relative,
        "command": redact_command(command),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "stdout_bytes": len(stdout),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_bytes": len(stderr),
        "stderr_sha256": sha256_bytes(stderr),
    }
    if execution_error:
        event["execution_error"] = execution_error
    event["command_sha256"] = canonical_command_sha256(event["command"])
    append_event(ledger_path, event)

    emit_bytes(sys.stdout, stdout)
    emit_bytes(sys.stderr, stderr)
    return exit_code


def record_artifact(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger).expanduser()
    ledger = load_ledger(ledger_path)
    original = Path(args.path).expanduser()
    if original.is_symlink():
        raise LedgerError("refusing to record a symlink artifact")
    artifact, artifact_relative = relative_to_ledger_root(ledger_path, original, "artifact")
    exists = artifact.is_file()
    label = require_trimmed_string(args.label, "label")
    event: dict[str, Any] = {
        "kind": "artifact",
        "artifact_kind": args.kind,
        "label": label,
        "run_id": ledger["run_id"],
        "recorded_at": now_iso(),
        "path": artifact_relative,
        "exists": exists,
    }
    if exists:
        try:
            content = artifact.read_bytes()
        except OSError as error:
            raise LedgerError(f"cannot read artifact: {error}") from error
        event.update({"bytes": len(content), "sha256": sha256_bytes(content)})
        if args.kind == "screenshot":
            media_type, width, height = screenshot_metadata(content)
            event.update({"media_type": media_type, "width": width, "height": height})

    context = {
        key: value.strip()
        for key, value in {
            "route": args.route,
            "viewport": args.viewport,
            "locale": args.locale,
            "state": args.state,
            "note": args.context,
        }.items()
        if isinstance(value, str) and value.strip()
    }
    if args.kind == "screenshot" and not all(context.get(key) for key in ("route", "viewport", "state")):
        raise LedgerError("screenshot requires --route, --viewport, and --state context")
    if context:
        event["context"] = context
    append_event(ledger_path, event)
    return 0 if exists else 1


def summarize(ledger: dict[str, Any]) -> dict[str, Any]:
    commands = [event for event in ledger["events"] if event.get("kind") == "command"]
    artifacts = [event for event in ledger["events"] if event.get("kind") == "artifact"]
    return {
        "schema_version": ledger["schema_version"],
        "case_id": ledger["case_id"],
        "run_id": ledger["run_id"],
        "command_count": len(commands),
        "command_passed": sum(event.get("exit_code") == 0 for event in commands),
        "command_failed": sum(event.get("exit_code") != 0 for event in commands),
        "artifact_count": len(artifacts),
        "artifact_present": sum(event.get("exists") is True for event in artifacts),
        "artifact_missing": sum(event.get("exists") is not True for event in artifacts),
        "latest_command_results": {
            event.get("label", ""): event.get("exit_code") for event in commands if event.get("label")
        },
    }


def summary_command(args: argparse.Namespace) -> int:
    ledger = load_ledger(Path(args.ledger).expanduser())
    print(json.dumps(summarize(ledger), ensure_ascii=False, indent=2))
    return 0


def check_command(args: argparse.Namespace) -> int:
    ledger_path = Path(args.ledger).expanduser()
    ledger = load_ledger(ledger_path)
    facts = summarize(ledger)
    failures: list[str] = []
    latest = facts["latest_command_results"]
    for label in args.require_label:
        if label not in latest:
            failures.append(f"missing command label: {label}")
        elif latest[label] != 0:
            failures.append(f"command label failed: {label} (exit {latest[label]})")

    latest_artifacts: dict[str, dict[str, Any]] = {}
    for event in ledger["events"]:
        if event.get("kind") == "artifact" and isinstance(event.get("label"), str):
            latest_artifacts[event["label"]] = event
    for label in args.require_artifact:
        event = latest_artifacts.get(label)
        if event is None or event.get("exists") is not True:
            failures.append(f"missing artifact label: {label}")
            continue
        mismatch = verify_artifact_event(event, ledger_path.resolve().parent)
        if mismatch:
            failures.append(f"artifact label changed: {label} ({mismatch})")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Evidence requirements satisfied.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a machine-generated frontend evidence ledger.")
    subparsers = parser.add_subparsers(dest="action", required=True)

    init_parser = subparsers.add_parser("init", help="initialize one evaluator-owned evidence run")
    init_parser.add_argument("--ledger", required=True)
    init_parser.add_argument("--case-id", required=True)
    init_parser.add_argument("--run-id", required=True)
    init_parser.set_defaults(handler=init_ledger)

    run_parser = subparsers.add_parser("run", help="execute a command without a shell and record facts")
    run_parser.add_argument("--ledger", required=True)
    run_parser.add_argument("--label", required=True)
    run_parser.add_argument("--cwd", default=".")
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    run_parser.set_defaults(handler=run_command)

    artifact_parser = subparsers.add_parser("artifact", help="hash and record an existing artifact")
    artifact_parser.add_argument("--ledger", required=True)
    artifact_parser.add_argument("--label", required=True)
    artifact_parser.add_argument("--kind", choices=("screenshot", "report", "trace", "other"), default="other")
    artifact_parser.add_argument("--path", required=True)
    artifact_parser.add_argument("--route")
    artifact_parser.add_argument("--viewport", help="CSS viewport, for example 390x844")
    artifact_parser.add_argument("--locale")
    artifact_parser.add_argument("--state")
    artifact_parser.add_argument("--context", help="additional bounded note")
    artifact_parser.set_defaults(handler=record_artifact)

    summary_parser = subparsers.add_parser("summary", help="print ledger facts")
    summary_parser.add_argument("--ledger", required=True)
    summary_parser.set_defaults(handler=summary_command)

    check_parser = subparsers.add_parser("check", help="require latest successful labels and present artifacts")
    check_parser.add_argument("--ledger", required=True)
    check_parser.add_argument("--require-label", action="append", default=[])
    check_parser.add_argument("--require-artifact", action="append", default=[])
    check_parser.set_defaults(handler=check_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except LedgerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
