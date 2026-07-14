#!/usr/bin/env python3
"""Fail-closed validator for IA manifests, wireframe plans, and XML sitemaps."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


MAX_JSON_BYTES = 5_000_000
MAX_SITEMAP_BYTES = 52_428_800
MAX_SITEMAP_URLS = 50_000
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOREM_RE = re.compile(r"\b(lorem ipsum|placeholder|todo|tbd)\b", re.IGNORECASE)
STATE_KEYS = {"default", "loading", "empty", "error", "success", "permission"}
TRIGGER_STATES = {
    "static": {"default"},
    "remote_data": {"default", "loading", "empty", "error"},
    "form": {"default", "error", "success"},
    "auth_guard": {"default", "loading", "permission"},
    "mutation": {"default", "loading", "error", "success"},
    "overlay": {"default"},
}
MANIFEST_ROOT_KEYS = {
    "schema_version", "manifest_id", "default_locale", "supported_locales",
    "approved_origins", "routes",
}
ROUTE_KEYS = {
    "id", "path", "parent_id", "page_type", "locale", "visibility", "roles",
    "primary_task", "lifecycle", "navigation", "discovery", "state_triggers",
    "redirect_to", "evidence",
}
NAVIGATION_KEYS = {"surfaces", "label", "publicly_linked"}
DISCOVERY_KEYS = {"indexing", "canonical_url", "include_in_sitemap", "lastmod", "alternate_route_ids"}
EVIDENCE_KEYS = {"status", "sources"}
PLAN_ROOT_KEYS = {
    "schema_version", "plan_id", "manifest_id", "manifest_sha256", "readiness",
    "fidelity", "evidence_boundary", "evidence_refs", "flows", "screens",
}
FLOW_KEYS = {"id", "audience_role", "goal", "entry_page_id", "start_step_id", "success_criteria", "steps", "alternate_paths", "exit_states", "unknowns"}
FLOW_STEP_KEYS = {"id", "page_id", "trigger", "result", "next_step_id", "required_state", "risk", "recovery"}
ALTERNATE_PATH_KEYS = {"condition", "from_step_id", "to_step_id", "recovery"}
EXIT_STATE_KEYS = {"id", "status", "description", "recovery"}
SCREEN_KEYS = {
    "id", "page_id", "locale", "audience_roles", "entry_context", "primary_task",
    "primary_action", "regions", "state_coverage", "interactions", "desktop", "mobile",
    "navigation_targets", "unknowns", "claims",
}
REGION_KEYS = {"id", "purpose", "priority", "essential", "content_fixture", "extreme_cases", "source_status"}
STATE_VALUE_KEYS = {"status", "reason", "recovery"}
INTERACTION_KEYS = {"id", "trigger", "target_region", "result", "feedback", "recovery", "keyboard", "touch"}
LAYOUT_KEYS = {"region_order", "layout_mode"}
MOBILE_KEYS = {"region_order", "layout_mode", "transformations", "equivalence_reason"}
TRANSFORMATION_KEYS = {"region_id", "action", "equivalent", "reason"}
CLAIM_KEYS = {"claim", "status", "evidence_ref"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    path: str
    message: str


class SitePlanInputError(ValueError):
    """Raised when an artifact cannot be read safely."""


def _finding(findings: list[Finding], code: str, path: str, message: str, severity: str = "P0") -> None:
    findings.append(Finding(code, severity, path, message))


def _read_bytes(path: Path, limit: int) -> bytes:
    if path.is_symlink():
        raise SitePlanInputError(f"refusing symlink: {path}")
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as error:
        raise SitePlanInputError(f"cannot read {path}: {error}") from error
    if len(data) > limit:
        raise SitePlanInputError(f"artifact exceeds {limit} bytes: {path}")
    return data


def _load_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_bytes(path, MAX_JSON_BYTES)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SitePlanInputError(f"invalid UTF-8 JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise SitePlanInputError(f"JSON root must be an object: {path}")
    return value, raw


def _exact_keys(value: Any, expected: set[str], path: str, findings: list[Finding], code: str) -> bool:
    if not isinstance(value, dict):
        _finding(findings, code, path, "must be an object")
        return False
    if set(value) != expected:
        missing = sorted(expected - set(value))
        unexpected = sorted(set(value) - expected)
        _finding(findings, code, path, f"key drift; missing={missing}, unexpected={unexpected}")
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalized_internal_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.startswith("/") or value.startswith("//"):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or "\\" in value or "\x00" in value:
        return None
    if any(part in {".", ".."} for part in parsed.path.split("/")):
        return None
    return "/" if parsed.path == "/" else parsed.path.rstrip("/")


def _origin(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        return None
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        return None
    return f"https://{parsed.netloc}"


def _approved_url(value: Any, approved_origins: set[str]) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
        and f"https://{parsed.netloc}" in approved_origins
    )


def _valid_lastmod(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value:
        return False
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_manifest(data: dict[str, Any]) -> tuple[list[Finding], dict[str, dict[str, Any]], set[str]]:
    findings: list[Finding] = []
    routes_by_id: dict[str, dict[str, Any]] = {}
    approved_origins: set[str] = set()
    if not _exact_keys(data, MANIFEST_ROOT_KEYS, "$", findings, "SM_ROOT_SCHEMA_INVALID"):
        return findings, routes_by_id, approved_origins
    if data["schema_version"] != 1:
        _finding(findings, "SM_SCHEMA_VERSION_UNSUPPORTED", "$.schema_version", "must equal 1")
    if not _nonempty(data["manifest_id"]) or ID_RE.fullmatch(data["manifest_id"]) is None:
        _finding(findings, "SM_MANIFEST_ID_INVALID", "$.manifest_id", "must be lowercase kebab-case")
    locales = data["supported_locales"]
    if not isinstance(locales, list) or not locales or len(locales) != len(set(locales)) or not all(_nonempty(item) for item in locales):
        _finding(findings, "SM_LOCALES_INVALID", "$.supported_locales", "must be a unique non-empty string array")
        locales = []
    if data["default_locale"] not in locales:
        _finding(findings, "SM_DEFAULT_LOCALE_UNKNOWN", "$.default_locale", "must appear in supported_locales")
    origins = data["approved_origins"]
    if not isinstance(origins, list) or not origins:
        _finding(findings, "SM_APPROVED_ORIGINS_INVALID", "$.approved_origins", "must be a non-empty array")
    else:
        for index, item in enumerate(origins):
            normalized = _origin(item)
            if normalized is None:
                _finding(findings, "SM_APPROVED_ORIGIN_INVALID", f"$.approved_origins[{index}]", "must be an HTTPS origin without credentials, path, query, or fragment")
            elif normalized in approved_origins:
                _finding(findings, "SM_APPROVED_ORIGIN_DUPLICATE", f"$.approved_origins[{index}]", "duplicate normalized origin")
            else:
                approved_origins.add(normalized)
    routes = data["routes"]
    if not isinstance(routes, list) or not routes:
        _finding(findings, "SM_ROUTES_INVALID", "$.routes", "must be a non-empty array")
        return findings, routes_by_id, approved_origins

    normalized_paths: dict[tuple[str, str], str] = {}
    for index, route in enumerate(routes):
        path = f"$.routes[{index}]"
        if not _exact_keys(route, ROUTE_KEYS, path, findings, "SM_ROUTE_SCHEMA_INVALID"):
            continue
        route_id = route["id"]
        if not _nonempty(route_id) or ID_RE.fullmatch(route_id) is None:
            _finding(findings, "SM_ROUTE_ID_INVALID", f"{path}.id", "must be lowercase kebab-case")
        elif route_id in routes_by_id:
            _finding(findings, "SM_ROUTE_ID_DUPLICATE", f"{path}.id", f"duplicate route id {route_id!r}")
        else:
            routes_by_id[route_id] = route
        normalized_path = _normalized_internal_path(route["path"])
        if normalized_path is None:
            _finding(findings, "SM_ROUTE_PATH_EXTERNAL", f"{path}.path", "must be a safe internal path without query or fragment")
        elif route["path"] != normalized_path:
            _finding(findings, "SM_ROUTE_PATH_NOT_NORMALIZED", f"{path}.path", f"use normalized path {normalized_path!r}")
        else:
            key = (str(route["locale"]), normalized_path)
            if key in normalized_paths:
                _finding(findings, "SM_ROUTE_PATH_DUPLICATE", f"{path}.path", f"duplicates {normalized_paths[key]!r} for the locale")
            else:
                normalized_paths[key] = str(route_id)
        if route["locale"] not in locales:
            _finding(findings, "SM_ROUTE_LOCALE_UNKNOWN", f"{path}.locale", "must appear in supported_locales")
        if route["visibility"] not in {"public", "authenticated", "role_restricted", "private"}:
            _finding(findings, "SM_VISIBILITY_INVALID", f"{path}.visibility", "unsupported visibility")
        if not isinstance(route["roles"], list) or len(route["roles"]) != len(set(route["roles"])) or not all(_nonempty(role) for role in route["roles"]):
            _finding(findings, "SM_ROLES_INVALID", f"{path}.roles", "must be a unique string array")
        if route["visibility"] == "role_restricted" and not route["roles"]:
            _finding(findings, "SM_ROLE_RESTRICTION_EMPTY", f"{path}.roles", "role_restricted routes need at least one role")
        if not _nonempty(route["primary_task"]):
            _finding(findings, "SM_PRIMARY_TASK_MISSING", f"{path}.primary_task", "must describe a user task")
        if route["lifecycle"] not in {"active", "draft", "retired", "redirect"}:
            _finding(findings, "SM_LIFECYCLE_INVALID", f"{path}.lifecycle", "unsupported lifecycle")
        if _exact_keys(route["navigation"], NAVIGATION_KEYS, f"{path}.navigation", findings, "SM_NAVIGATION_SCHEMA_INVALID"):
            nav = route["navigation"]
            surfaces = nav["surfaces"]
            allowed_surfaces = {"primary", "secondary", "contextual", "footer", "none"}
            if not isinstance(surfaces, list) or not surfaces or len(surfaces) != len(set(surfaces)) or not set(surfaces) <= allowed_surfaces or ("none" in surfaces and len(surfaces) > 1):
                _finding(findings, "SM_NAVIGATION_SURFACE_INVALID", f"{path}.navigation.surfaces", "invalid or conflicting surfaces")
            if not isinstance(nav["publicly_linked"], bool):
                _finding(findings, "SM_PUBLIC_LINK_FLAG_INVALID", f"{path}.navigation.publicly_linked", "must be boolean")
            if nav["publicly_linked"] and route["visibility"] != "public":
                _finding(findings, "SM_PRIVATE_ROUTE_PUBLICLY_LINKED", f"{path}.navigation.publicly_linked", "non-public routes cannot appear in public navigation")
        if _exact_keys(route["discovery"], DISCOVERY_KEYS, f"{path}.discovery", findings, "SM_DISCOVERY_SCHEMA_INVALID"):
            discovery = route["discovery"]
            if discovery["indexing"] not in {"index", "noindex"}:
                _finding(findings, "SM_INDEXING_INVALID", f"{path}.discovery.indexing", "must be index or noindex")
            if not isinstance(discovery["include_in_sitemap"], bool):
                _finding(findings, "SM_SITEMAP_FLAG_INVALID", f"{path}.discovery.include_in_sitemap", "must be boolean")
            if not _valid_lastmod(discovery["lastmod"]):
                _finding(findings, "SM_LASTMOD_INVALID", f"{path}.discovery.lastmod", "must be an ISO date or datetime")
            if discovery["canonical_url"] is not None and not _approved_url(discovery["canonical_url"], approved_origins):
                _finding(findings, "SM_CANONICAL_INVALID", f"{path}.discovery.canonical_url", "must be an HTTPS URL on an approved origin")
            if discovery["include_in_sitemap"] and (discovery["indexing"] != "index" or route["visibility"] != "public" or route["lifecycle"] != "active"):
                _finding(findings, "SM_NONINDEXABLE_IN_SITEMAP", f"{path}.discovery.include_in_sitemap", "only active public indexable routes may enter the sitemap")
            if discovery["indexing"] == "index" and route["visibility"] != "public":
                _finding(findings, "SM_PRIVATE_ROUTE_INDEXABLE", f"{path}.discovery.indexing", "non-public routes must be noindex")
            if route["lifecycle"] == "active" and route["visibility"] == "public" and discovery["indexing"] == "index" and not _approved_url(discovery["canonical_url"], approved_origins):
                _finding(findings, "SM_INDEXABLE_CANONICAL_MISSING", f"{path}.discovery.canonical_url", "active public indexable routes need an approved canonical URL")
            alternates = discovery["alternate_route_ids"]
            if not isinstance(alternates, list) or len(alternates) != len(set(alternates)) or not all(_nonempty(item) for item in alternates):
                _finding(findings, "SM_ALTERNATES_INVALID", f"{path}.discovery.alternate_route_ids", "must be a unique string array")
        triggers = route["state_triggers"]
        if not isinstance(triggers, list) or not triggers or len(triggers) != len(set(triggers)) or not set(triggers) <= set(TRIGGER_STATES):
            _finding(findings, "SM_STATE_TRIGGERS_INVALID", f"{path}.state_triggers", "contains missing, duplicate, or unsupported triggers")
        elif "static" in triggers and len(triggers) > 1:
            _finding(findings, "WF_STATE_TRIGGER_CONFLICT", f"{path}.state_triggers", "static cannot be combined with dynamic triggers")
        if route["lifecycle"] == "redirect":
            if not _nonempty(route["redirect_to"]):
                _finding(findings, "SM_REDIRECT_TARGET_MISSING", f"{path}.redirect_to", "redirect routes need a target route id")
            elif _normalized_internal_path(route["redirect_to"]) is not None or urlsplit(route["redirect_to"]).scheme or route["redirect_to"].startswith("//"):
                _finding(findings, "SM_REDIRECT_TARGET_FORBIDDEN", f"{path}.redirect_to", "redirect_to must reference an internal route id, never a URL or path")
        elif route["redirect_to"] is not None:
            _finding(findings, "SM_REDIRECT_TARGET_UNEXPECTED", f"{path}.redirect_to", "only redirect lifecycle may define redirect_to")
        if _exact_keys(route["evidence"], EVIDENCE_KEYS, f"{path}.evidence", findings, "SM_EVIDENCE_SCHEMA_INVALID"):
            evidence = route["evidence"]
            if evidence["status"] not in {"provided", "observed", "hypothesis", "unknown"}:
                _finding(findings, "SM_EVIDENCE_STATUS_INVALID", f"{path}.evidence.status", "unsupported evidence status")
            if not isinstance(evidence["sources"], list) or len(evidence["sources"]) != len(set(evidence["sources"])) or not all(_nonempty(item) for item in evidence["sources"]):
                _finding(findings, "SM_EVIDENCE_SOURCES_INVALID", f"{path}.evidence.sources", "must be a unique string array")

    for route_id, route in routes_by_id.items():
        parent_id = route["parent_id"]
        if parent_id is not None and parent_id not in routes_by_id:
            _finding(findings, "SM_PARENT_UNKNOWN", f"$.routes[{route_id}].parent_id", f"unknown parent {parent_id!r}")
        if route["lifecycle"] == "redirect" and _nonempty(route["redirect_to"]) and route["redirect_to"] not in routes_by_id:
            _finding(findings, "SM_REDIRECT_TARGET_UNKNOWN", f"$.routes[{route_id}].redirect_to", "target route id does not exist")
        discovery = route["discovery"] if isinstance(route["discovery"], dict) else {}
        for alternate_id in discovery.get("alternate_route_ids", []) if isinstance(discovery.get("alternate_route_ids", []), list) else []:
            alternate = routes_by_id.get(alternate_id)
            if alternate is None:
                _finding(findings, "SM_ALTERNATE_UNKNOWN", f"$.routes[{route_id}].discovery.alternate_route_ids", f"unknown alternate {alternate_id!r}")
            elif route_id not in alternate.get("discovery", {}).get("alternate_route_ids", []):
                _finding(findings, "SM_HREFLANG_RECIPROCAL_MISSING", f"$.routes[{route_id}].discovery.alternate_route_ids", f"alternate {alternate_id!r} is not reciprocal")
            elif alternate.get("locale") == route.get("locale"):
                _finding(findings, "SM_ALTERNATE_LOCALE_CONFLICT", f"$.routes[{route_id}].discovery.alternate_route_ids", "alternate routes must use different locales")
        if route["visibility"] == "public" and route["lifecycle"] == "active" and route["path"] != "/":
            nav = route["navigation"] if isinstance(route["navigation"], dict) else {}
            if route["parent_id"] is None and not nav.get("publicly_linked", False):
                _finding(findings, "SM_ROUTE_ORPHAN", f"$.routes[{route_id}]", "public route has no parent or public navigation path")

    def _find_cycle(field: str, eligible: Iterable[str], code: str) -> None:
        for start in eligible:
            seen: set[str] = set()
            current: str | None = start
            while current in routes_by_id:
                if current in seen:
                    _finding(findings, code, f"$.routes[{start}].{field}", f"cycle includes {current!r}")
                    break
                seen.add(current)
                next_value = routes_by_id[current].get(field)
                current = next_value if isinstance(next_value, str) else None

    _find_cycle("parent_id", routes_by_id, "SM_PARENT_CYCLE")
    redirect_ids = [key for key, route in routes_by_id.items() if route.get("lifecycle") == "redirect"]
    _find_cycle("redirect_to", redirect_ids, "SM_REDIRECT_CYCLE")
    return findings, routes_by_id, approved_origins


def validate_wireframe(data: dict[str, Any], manifest: dict[str, Any], manifest_raw: bytes, routes_by_id: dict[str, dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    if not _exact_keys(data, PLAN_ROOT_KEYS, "$", findings, "WF_ROOT_SCHEMA_INVALID"):
        return findings
    if data["schema_version"] != 1:
        _finding(findings, "WF_SCHEMA_VERSION_UNSUPPORTED", "$.schema_version", "must equal 1")
    if not _nonempty(data["plan_id"]) or ID_RE.fullmatch(data["plan_id"]) is None:
        _finding(findings, "WF_PLAN_ID_INVALID", "$.plan_id", "must be lowercase kebab-case")
    if data["manifest_id"] != manifest.get("manifest_id"):
        _finding(findings, "X_MANIFEST_ID_MISMATCH", "$.manifest_id", "does not match the site manifest")
    expected_hash = hashlib.sha256(manifest_raw).hexdigest()
    if data["manifest_sha256"] != expected_hash:
        _finding(findings, "X_MANIFEST_HASH_MISMATCH", "$.manifest_sha256", f"expected {expected_hash}")
    if data["readiness"] not in {"draft", "implementation_ready"}:
        _finding(findings, "WF_READINESS_INVALID", "$.readiness", "unsupported readiness")
    if data["fidelity"] not in {"structural", "wireflow", "interactive_responsive"}:
        _finding(findings, "WF_FIDELITY_INVALID", "$.fidelity", "unsupported fidelity")
    boundary = data["evidence_boundary"]
    if not isinstance(boundary, dict) or boundary.get("status") != "planning_only" or boundary.get("self_certified") is not False or set(boundary) != {"status", "self_certified"}:
        _finding(findings, "WF_SELF_CERTIFICATION_FORBIDDEN", "$.evidence_boundary", "must be planning_only with self_certified=false")
    refs = data["evidence_refs"]
    if not isinstance(refs, list) or len(refs) != len(set(refs)) or not all(_nonempty(item) for item in refs):
        _finding(findings, "WF_EVIDENCE_REFS_INVALID", "$.evidence_refs", "must be a unique string array")
        refs = []
    screens = data["screens"]
    if not isinstance(screens, list) or not screens:
        _finding(findings, "WF_SCREENS_INVALID", "$.screens", "must be a non-empty array")
        return findings
    screen_ids: set[str] = set()
    page_ids: set[str] = set()
    screen_states_by_page: dict[str, dict[str, Any]] = {}
    for index, screen in enumerate(screens):
        path = f"$.screens[{index}]"
        if not _exact_keys(screen, SCREEN_KEYS, path, findings, "WF_SCREEN_SCHEMA_INVALID"):
            continue
        screen_id = screen["id"]
        if not _nonempty(screen_id) or ID_RE.fullmatch(screen_id) is None:
            _finding(findings, "WF_SCREEN_ID_INVALID", f"{path}.id", "must be lowercase kebab-case")
        elif screen_id in screen_ids:
            _finding(findings, "WF_SCREEN_ID_DUPLICATE", f"{path}.id", "duplicate screen id")
        else:
            screen_ids.add(screen_id)
        page_id = screen["page_id"]
        if page_id in page_ids:
            _finding(findings, "X_WIREFRAME_ROUTE_DUPLICATE", f"{path}.page_id", "each route may have only one screen plan")
        else:
            page_ids.add(page_id)
        route = routes_by_id.get(page_id)
        if route is None:
            _finding(findings, "X_WIREFRAME_ROUTE_UNKNOWN", f"{path}.page_id", "route does not exist in the site manifest")
        else:
            if route.get("lifecycle") != "active":
                _finding(findings, "X_WIREFRAME_ROUTE_NOT_RENDERABLE", f"{path}.page_id", "screen must target an active route")
            if screen["locale"] != route.get("locale"):
                _finding(findings, "X_WIREFRAME_LOCALE_MISMATCH", f"{path}.locale", "screen locale differs from route locale")
            if set(screen["audience_roles"]) != set(route.get("roles", [])):
                _finding(findings, "X_WIREFRAME_ROLES_MISMATCH", f"{path}.audience_roles", "screen roles differ from route roles")
            if screen["primary_task"] != route.get("primary_task"):
                _finding(findings, "X_WIREFRAME_TASK_MISMATCH", f"{path}.primary_task", "screen task differs from route task")
        for field in ("entry_context", "primary_task", "primary_action"):
            if not _nonempty(screen[field]):
                _finding(findings, "WF_REQUIRED_TEXT_MISSING", f"{path}.{field}", "must be non-empty")
        regions = screen["regions"]
        region_ids: set[str] = set()
        essential: dict[str, bool] = {}
        priorities: set[int] = set()
        if not isinstance(regions, list) or not regions:
            _finding(findings, "WF_REGIONS_INVALID", f"{path}.regions", "must be a non-empty array")
            regions = []
        for region_index, region in enumerate(regions):
            region_path = f"{path}.regions[{region_index}]"
            if not _exact_keys(region, REGION_KEYS, region_path, findings, "WF_REGION_SCHEMA_INVALID"):
                continue
            region_id = region["id"]
            if not _nonempty(region_id) or region_id in region_ids:
                _finding(findings, "WF_REGION_ID_INVALID", f"{region_path}.id", "must be non-empty and unique")
            else:
                region_ids.add(region_id)
                essential[region_id] = region["essential"] is True
            if not isinstance(region["priority"], int) or region["priority"] < 1 or region["priority"] in priorities:
                _finding(findings, "WF_REGION_PRIORITY_INVALID", f"{region_path}.priority", "must be a unique positive integer")
            else:
                priorities.add(region["priority"])
            if not _nonempty(region["purpose"]):
                _finding(findings, "WF_REGION_PURPOSE_MISSING", f"{region_path}.purpose", "must be non-empty")
            if not _nonempty(region["content_fixture"]) or LOREM_RE.search(str(region["content_fixture"])):
                _finding(findings, "WF_CONTENT_FIXTURE_FAKE", f"{region_path}.content_fixture", "use representative content, not placeholder prose")
            if not isinstance(region["extreme_cases"], list) or not region["extreme_cases"] or not all(_nonempty(item) for item in region["extreme_cases"]):
                _finding(findings, "WF_EXTREME_CASE_MISSING", f"{region_path}.extreme_cases", "record at least one realistic extreme")
            if region["source_status"] not in {"provided", "observed", "hypothesis", "unknown"}:
                _finding(findings, "WF_SOURCE_STATUS_INVALID", f"{region_path}.source_status", "unsupported source status")
        states = screen["state_coverage"]
        if not isinstance(states, dict) or set(states) != STATE_KEYS:
            _finding(findings, "WF_STATE_SCHEMA_INVALID", f"{path}.state_coverage", f"must contain exactly {sorted(STATE_KEYS)}")
            states = {}
        for state_name, state in states.items():
            state_path = f"{path}.state_coverage.{state_name}"
            if not _exact_keys(state, STATE_VALUE_KEYS, state_path, findings, "WF_STATE_VALUE_INVALID"):
                continue
            if state["status"] not in {"designed", "not_applicable", "unknown"} or not _nonempty(state["reason"]) or not _nonempty(state["recovery"]):
                _finding(findings, "WF_STATE_VALUE_INVALID", state_path, "status, reason, and recovery must be explicit")
        screen_states_by_page[page_id] = states
        if route is not None:
            required_states = set().union(*(TRIGGER_STATES.get(trigger, set()) for trigger in route.get("state_triggers", [])))
            if data["readiness"] == "implementation_ready":
                for state_name in sorted(required_states):
                    if states.get(state_name, {}).get("status") != "designed":
                        _finding(findings, "WF_REQUIRED_STATE_MISSING", f"{path}.state_coverage.{state_name}", f"route triggers require designed {state_name!r} state")
        interactions = screen["interactions"]
        interaction_ids: set[str] = set()
        if not isinstance(interactions, list):
            _finding(findings, "WF_INTERACTIONS_INVALID", f"{path}.interactions", "must be an array")
            interactions = []
        if data["fidelity"] in {"wireflow", "interactive_responsive"} and not interactions:
            _finding(findings, "WF_INTERACTION_MISSING", f"{path}.interactions", "wireflow fidelity needs at least one interaction")
        for interaction_index, interaction in enumerate(interactions):
            interaction_path = f"{path}.interactions[{interaction_index}]"
            if not _exact_keys(interaction, INTERACTION_KEYS, interaction_path, findings, "WF_INTERACTION_SCHEMA_INVALID"):
                continue
            if not _nonempty(interaction["id"]) or interaction["id"] in interaction_ids:
                _finding(findings, "WF_INTERACTION_ID_INVALID", f"{interaction_path}.id", "must be non-empty and unique")
            else:
                interaction_ids.add(interaction["id"])
            if interaction["target_region"] not in region_ids:
                _finding(findings, "WF_INTERACTION_TARGET_UNKNOWN", f"{interaction_path}.target_region", "must reference a screen region")
            for field in ("trigger", "result", "feedback", "recovery", "keyboard"):
                if not _nonempty(interaction[field]):
                    _finding(findings, "WF_INTERACTION_DETAIL_MISSING", f"{interaction_path}.{field}", "must be non-empty")
            if not _nonempty(interaction["touch"]):
                _finding(findings, "WF_TOUCH_FALLBACK_MISSING", f"{interaction_path}.touch", "must define a touch path")
        desktop = screen["desktop"]
        if not _exact_keys(desktop, LAYOUT_KEYS, f"{path}.desktop", findings, "WF_DESKTOP_SCHEMA_INVALID"):
            desktop = {}
        mobile = screen["mobile"]
        if not _exact_keys(mobile, MOBILE_KEYS, f"{path}.mobile", findings, "WF_MOBILE_SCHEMA_INVALID"):
            mobile = {}
        for label, layout in (("desktop", desktop), ("mobile", mobile)):
            order = layout.get("region_order", [])
            if not isinstance(order, list) or len(order) != len(set(order)) or set(order) != region_ids:
                _finding(findings, "WF_REGION_ORDER_INVALID", f"{path}.{label}.region_order", "must include each region exactly once")
            if not _nonempty(layout.get("layout_mode")):
                _finding(findings, "WF_LAYOUT_MODE_MISSING", f"{path}.{label}.layout_mode", "must describe composition")
        transformations = mobile.get("transformations", [])
        transformed: set[str] = set()
        actions: list[str] = []
        if not isinstance(transformations, list):
            _finding(findings, "WF_MOBILE_TRANSFORMATIONS_INVALID", f"{path}.mobile.transformations", "must be an array")
            transformations = []
        for transform_index, transform in enumerate(transformations):
            transform_path = f"{path}.mobile.transformations[{transform_index}]"
            if not _exact_keys(transform, TRANSFORMATION_KEYS, transform_path, findings, "WF_MOBILE_TRANSFORMATION_SCHEMA_INVALID"):
                continue
            region_id = transform["region_id"]
            if region_id not in region_ids or region_id in transformed:
                _finding(findings, "WF_MOBILE_TRANSFORMATION_REGION_INVALID", f"{transform_path}.region_id", "must reference each region once")
            else:
                transformed.add(region_id)
            action = transform["action"]
            actions.append(action)
            if action not in {"preserve", "reorder", "replace", "condense", "defer", "remove", "move_to_thumb_reach"}:
                _finding(findings, "WF_MOBILE_TRANSFORMATION_ACTION_INVALID", f"{transform_path}.action", "unsupported action")
            if not _nonempty(transform["equivalent"]) or not _nonempty(transform["reason"]):
                _finding(findings, "WF_MOBILE_EQUIVALENCE_MISSING", transform_path, "equivalent and reason must be explicit")
            if essential.get(region_id) and action in {"defer", "remove"} and len(str(transform["equivalent"]).strip()) < 8:
                _finding(findings, "WF_ESSENTIAL_MOBILE_ACCESS_MISSING", f"{transform_path}.equivalent", "essential regions need a concrete equivalent access path")
        if transformed != region_ids:
            _finding(findings, "WF_MOBILE_TRANSFORMATION_MISSING", f"{path}.mobile.transformations", "every desktop region needs an explicit mobile transformation")
        mobile_text = json.dumps(mobile, ensure_ascii=False).lower()
        if re.search(r"\b(scale|scaled|zoom|shrink|縮放|縮小桌面)\b", mobile_text):
            _finding(findings, "WF_MOBILE_SCALE_FORBIDDEN", f"{path}.mobile", "mobile cannot be a scaled desktop canvas")
        if len(region_ids) >= 3 and route is not None and route.get("page_type") in {"dashboard", "product", "commerce", "form"}:
            stack_only = actions and set(actions) == {"preserve"}
            same_order = desktop.get("region_order") == mobile.get("region_order")
            mode = str(mobile.get("layout_mode", "")).lower()
            if stack_only or (same_order and re.search(r"stack|直式|單欄", mode)):
                _finding(findings, "WF_MOBILE_TRANSFORMATION_MISSING", f"{path}.mobile", "complex product surfaces need a material mobile transformation")
        if not _nonempty(mobile.get("equivalence_reason")):
            _finding(findings, "WF_MOBILE_EQUIVALENCE_MISSING", f"{path}.mobile.equivalence_reason", "must explain task equivalence")
        targets = screen["navigation_targets"]
        if not isinstance(targets, list) or len(targets) != len(set(targets)):
            _finding(findings, "WF_NAVIGATION_TARGETS_INVALID", f"{path}.navigation_targets", "must be a unique array")
        else:
            for target in targets:
                if target not in routes_by_id:
                    _finding(findings, "WF_NAVIGATION_TARGET_UNKNOWN", f"{path}.navigation_targets", f"unknown route {target!r}")
        if not isinstance(screen["unknowns"], list) or len(screen["unknowns"]) != len(set(screen["unknowns"])) or not all(_nonempty(item) for item in screen["unknowns"]):
            _finding(findings, "WF_UNKNOWNS_INVALID", f"{path}.unknowns", "must be a unique string array")
        claims = screen["claims"]
        if not isinstance(claims, list):
            _finding(findings, "WF_CLAIMS_INVALID", f"{path}.claims", "must be an array")
            claims = []
        for claim_index, claim in enumerate(claims):
            claim_path = f"{path}.claims[{claim_index}]"
            if not _exact_keys(claim, CLAIM_KEYS, claim_path, findings, "WF_CLAIM_SCHEMA_INVALID"):
                continue
            if claim["status"] not in {"HYPOTHESIS", "UNVERIFIED"}:
                _finding(findings, "WF_SELF_CERTIFICATION_FORBIDDEN", f"{claim_path}.status", "wireframes cannot mark their own claims verified")
            if claim["evidence_ref"] not in refs:
                _finding(findings, "X_EVIDENCE_REF_UNKNOWN", f"{claim_path}.evidence_ref", "claim must reference a declared evidence source")
            if not _nonempty(claim["claim"]):
                _finding(findings, "WF_CLAIM_TEXT_MISSING", f"{claim_path}.claim", "must be non-empty")

    flows = data["flows"]
    flow_ids: set[str] = set()
    flow_page_ids: set[str] = set()
    if not isinstance(flows, list) or not flows:
        _finding(findings, "UF_FLOWS_INVALID", "$.flows", "must be a non-empty array")
        flows = []
    for flow_index, flow in enumerate(flows):
        flow_path = f"$.flows[{flow_index}]"
        if not _exact_keys(flow, FLOW_KEYS, flow_path, findings, "UF_FLOW_SCHEMA_INVALID"):
            continue
        flow_id = flow["id"]
        if not _nonempty(flow_id) or ID_RE.fullmatch(flow_id) is None or flow_id in flow_ids:
            _finding(findings, "UF_FLOW_ID_INVALID", f"{flow_path}.id", "must be unique lowercase kebab-case")
        else:
            flow_ids.add(flow_id)
        for field in ("audience_role", "goal", "entry_page_id", "start_step_id", "success_criteria"):
            if not _nonempty(flow[field]):
                _finding(findings, "UF_REQUIRED_TEXT_MISSING", f"{flow_path}.{field}", "must be non-empty")
        entry_route = routes_by_id.get(flow["entry_page_id"])
        if entry_route is None:
            _finding(findings, "UF_ENTRY_ROUTE_UNKNOWN", f"{flow_path}.entry_page_id", "must reference an existing route")
        elif flow["audience_role"] not in entry_route.get("roles", []):
            _finding(findings, "UF_AUDIENCE_ROLE_MISMATCH", f"{flow_path}.audience_role", "role must be allowed by the entry route")
        steps = flow["steps"]
        step_by_id: dict[str, dict[str, Any]] = {}
        if not isinstance(steps, list) or not steps:
            _finding(findings, "UF_STEPS_INVALID", f"{flow_path}.steps", "must be a non-empty array")
            steps = []
        for step_index, step in enumerate(steps):
            step_path = f"{flow_path}.steps[{step_index}]"
            if not _exact_keys(step, FLOW_STEP_KEYS, step_path, findings, "UF_STEP_SCHEMA_INVALID"):
                continue
            step_id = step["id"]
            if not _nonempty(step_id) or step_id in step_by_id:
                _finding(findings, "UF_STEP_ID_INVALID", f"{step_path}.id", "must be non-empty and unique within the flow")
            else:
                step_by_id[step_id] = step
            page_id = step["page_id"]
            route = routes_by_id.get(page_id)
            if route is None or route.get("lifecycle") != "active":
                _finding(findings, "UF_STEP_PAGE_UNKNOWN", f"{step_path}.page_id", "must reference an active route")
            else:
                flow_page_ids.add(page_id)
                if flow["audience_role"] not in route.get("roles", []):
                    _finding(findings, "UF_STEP_ROLE_MISMATCH", f"{step_path}.page_id", "flow role is not allowed by this route")
            for field in ("trigger", "result", "risk", "recovery"):
                if not _nonempty(step[field]):
                    _finding(findings, "UF_STEP_DETAIL_MISSING", f"{step_path}.{field}", "must describe user action, system response, risk, and recovery")
            required_state = step["required_state"]
            if required_state not in STATE_KEYS:
                _finding(findings, "UF_STEP_STATE_INVALID", f"{step_path}.required_state", "unsupported state")
            elif screen_states_by_page.get(page_id, {}).get(required_state, {}).get("status") != "designed":
                _finding(findings, "UF_STEP_STATE_UNCOVERED", f"{step_path}.required_state", "referenced screen state must be designed")
            if step["next_step_id"] is not None and not _nonempty(step["next_step_id"]):
                _finding(findings, "UF_NEXT_STEP_INVALID", f"{step_path}.next_step_id", "must be a step id or null")
        start_id = flow["start_step_id"]
        if start_id not in step_by_id:
            _finding(findings, "UF_START_STEP_UNKNOWN", f"{flow_path}.start_step_id", "must reference a flow step")
        for step_id, step in step_by_id.items():
            next_id = step["next_step_id"]
            if next_id is not None and next_id not in step_by_id:
                _finding(findings, "UF_NEXT_STEP_UNKNOWN", f"{flow_path}.steps[{step_id}].next_step_id", f"unknown next step {next_id!r}")
        reachable: set[str] = set()
        current = start_id if start_id in step_by_id else None
        terminal_reached = False
        while current is not None and current in step_by_id:
            if current in reachable:
                _finding(findings, "UF_PRIMARY_CYCLE", f"{flow_path}.steps", f"primary path cycles at {current!r}")
                break
            reachable.add(current)
            current = step_by_id[current]["next_step_id"]
            if current is None:
                terminal_reached = True
        if step_by_id and not terminal_reached and start_id in step_by_id:
            _finding(findings, "UF_TERMINAL_MISSING", f"{flow_path}.steps", "primary path must reach a null terminal step")
        for unreachable in sorted(set(step_by_id) - reachable):
            _finding(findings, "UF_STEP_UNREACHABLE", f"{flow_path}.steps[{unreachable}]", "step is unreachable from start_step_id")
        alternate_paths = flow["alternate_paths"]
        if not isinstance(alternate_paths, list) or not alternate_paths:
            _finding(findings, "UF_HAPPY_PATH_ONLY", f"{flow_path}.alternate_paths", "implementation planning needs at least one important alternate or recovery path")
            alternate_paths = []
        for alternate_index, alternate in enumerate(alternate_paths):
            alternate_path = f"{flow_path}.alternate_paths[{alternate_index}]"
            if not _exact_keys(alternate, ALTERNATE_PATH_KEYS, alternate_path, findings, "UF_ALTERNATE_PATH_INVALID"):
                continue
            if alternate["from_step_id"] not in step_by_id or alternate["to_step_id"] not in step_by_id:
                _finding(findings, "UF_ALTERNATE_PATH_INVALID", alternate_path, "from/to must reference steps in this flow")
            if not _nonempty(alternate["condition"]) or not _nonempty(alternate["recovery"]):
                _finding(findings, "UF_ALTERNATE_PATH_INVALID", alternate_path, "condition and recovery must be explicit")
        exit_states = flow["exit_states"]
        exit_ids: set[str] = set()
        exit_statuses: set[str] = set()
        if not isinstance(exit_states, list) or not exit_states:
            _finding(findings, "UF_EXIT_STATE_MISSING", f"{flow_path}.exit_states", "must include success and non-success exits")
            exit_states = []
        for exit_index, exit_state in enumerate(exit_states):
            exit_path = f"{flow_path}.exit_states[{exit_index}]"
            if not _exact_keys(exit_state, EXIT_STATE_KEYS, exit_path, findings, "UF_EXIT_STATE_INVALID"):
                continue
            if not _nonempty(exit_state["id"]) or exit_state["id"] in exit_ids:
                _finding(findings, "UF_EXIT_STATE_INVALID", f"{exit_path}.id", "must be non-empty and unique")
            else:
                exit_ids.add(exit_state["id"])
            if exit_state["status"] not in {"success", "abandoned", "blocked", "recoverable_error"}:
                _finding(findings, "UF_EXIT_STATE_INVALID", f"{exit_path}.status", "unsupported status")
            else:
                exit_statuses.add(exit_state["status"])
            if not _nonempty(exit_state["description"]) or not _nonempty(exit_state["recovery"]):
                _finding(findings, "UF_EXIT_STATE_INVALID", exit_path, "description and recovery must be explicit")
        if "success" not in exit_statuses or not exit_statuses.intersection({"abandoned", "blocked", "recoverable_error"}):
            _finding(findings, "UF_HAPPY_PATH_ONLY", f"{flow_path}.exit_states", "must include both success and a non-success exit")
        if not isinstance(flow["unknowns"], list) or len(flow["unknowns"]) != len(set(flow["unknowns"])) or not all(_nonempty(item) for item in flow["unknowns"]):
            _finding(findings, "UF_UNKNOWNS_INVALID", f"{flow_path}.unknowns", "must be a unique string array")
    if data["readiness"] == "implementation_ready":
        expected_pages = {route_id for route_id, route in routes_by_id.items() if route.get("lifecycle") == "active"}
        for route_id in sorted(expected_pages - page_ids):
            _finding(findings, "X_RENDERABLE_ROUTE_PLAN_MISSING", "$.screens", f"active route {route_id!r} has no wireframe screen")
        for route_id in sorted(expected_pages - flow_page_ids):
            _finding(findings, "X_ACTIVE_ROUTE_FLOW_MISSING", "$.flows", f"active route {route_id!r} does not participate in any user flow")
    return findings


def _read_sitemap(path: Path) -> bytes:
    if path.is_symlink():
        raise SitePlanInputError(f"refusing symlink: {path}")
    try:
        if path.suffix.lower() == ".gz":
            with gzip.open(path, "rb") as handle:
                data = handle.read(MAX_SITEMAP_BYTES + 1)
        else:
            data = _read_bytes(path, MAX_SITEMAP_BYTES)
    except (OSError, EOFError) as error:
        raise SitePlanInputError(f"cannot read sitemap {path}: {error}") from error
    if len(data) > MAX_SITEMAP_BYTES:
        raise SitePlanInputError(f"uncompressed sitemap exceeds {MAX_SITEMAP_BYTES} bytes: {path}")
    if re.search(br"<!\s*(DOCTYPE|ENTITY)\b", data, re.IGNORECASE):
        raise SitePlanInputError(f"DTD and ENTITY declarations are forbidden: {path}")
    return data


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_urlset(path: Path, approved_origins: set[str], findings: list[Finding]) -> dict[str, str | None]:
    raw = _read_sitemap(path)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise SitePlanInputError(f"invalid sitemap XML in {path}: {error}") from error
    if _local_name(root.tag) != "urlset":
        _finding(findings, "XS_ROOT_INVALID", str(path), "child sitemap must use urlset")
        return {}
    entries: dict[str, str | None] = {}
    urls = [child for child in root if _local_name(child.tag) == "url"]
    if len(urls) > MAX_SITEMAP_URLS:
        _finding(findings, "XS_URL_LIMIT_EXCEEDED", str(path), f"contains more than {MAX_SITEMAP_URLS} URLs")
    for index, item in enumerate(urls):
        loc_values = [(child.text or "").strip() for child in item if _local_name(child.tag) == "loc"]
        lastmod_values = [(child.text or "").strip() for child in item if _local_name(child.tag) == "lastmod"]
        entry_path = f"{path}:url[{index}]"
        if len(loc_values) != 1 or not _approved_url(loc_values[0], approved_origins):
            _finding(findings, "XS_LOC_INVALID", entry_path, "loc must be one absolute canonical HTTPS URL on an approved origin")
            continue
        loc = loc_values[0]
        if loc in entries:
            _finding(findings, "XS_LOC_DUPLICATE", entry_path, f"duplicate loc {loc!r}")
            continue
        if len(lastmod_values) > 1 or (lastmod_values and not _valid_lastmod(lastmod_values[0])):
            _finding(findings, "XS_LASTMOD_INVALID", entry_path, "lastmod must be one valid ISO date or datetime")
        entries[loc] = lastmod_values[0] if lastmod_values else None
    return entries


def validate_sitemaps(paths: list[Path], manifest: dict[str, Any], approved_origins: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    if not paths:
        return findings
    first_raw = _read_sitemap(paths[0])
    try:
        first_root = ET.fromstring(first_raw)
    except ET.ParseError as error:
        raise SitePlanInputError(f"invalid sitemap XML in {paths[0]}: {error}") from error
    entries: dict[str, str | None] = {}
    if _local_name(first_root.tag) == "urlset":
        if len(paths) != 1:
            _finding(findings, "XS_UNUSED_CHILD_SITEMAP", str(paths[1]), "extra sitemap files require a sitemapindex as the first file")
        entries.update(_parse_urlset(paths[0], approved_origins, findings))
    elif _local_name(first_root.tag) == "sitemapindex":
        provided = {path.name: path for path in paths[1:]}
        referenced: set[str] = set()
        for index, item in enumerate(child for child in first_root if _local_name(child.tag) == "sitemap"):
            locs = [(child.text or "").strip() for child in item if _local_name(child.tag) == "loc"]
            if len(locs) != 1 or not _approved_url(locs[0], approved_origins):
                _finding(findings, "XS_INDEX_LOC_INVALID", f"{paths[0]}:sitemap[{index}]", "loc must be one approved HTTPS URL")
                continue
            name = Path(urlsplit(locs[0]).path).name
            referenced.add(name)
            child_path = provided.get(name)
            if child_path is None:
                _finding(findings, "XS_INDEX_CHILD_MISSING", f"{paths[0]}:sitemap[{index}]", f"provide local child sitemap {name!r}; network fetching is forbidden")
                continue
            child_entries = _parse_urlset(child_path, approved_origins, findings)
            for loc, lastmod in child_entries.items():
                if loc in entries:
                    _finding(findings, "XS_LOC_DUPLICATE", str(child_path), f"duplicate loc across child sitemaps: {loc!r}")
                else:
                    entries[loc] = lastmod
        for name in sorted(set(provided) - referenced):
            _finding(findings, "XS_UNUSED_CHILD_SITEMAP", str(provided[name]), "child sitemap is not referenced by the index")
    else:
        _finding(findings, "XS_ROOT_INVALID", str(paths[0]), "root must be urlset or sitemapindex")
        return findings

    expected: dict[str, str | None] = {}
    for route in manifest.get("routes", []):
        discovery = route.get("discovery", {}) if isinstance(route, dict) else {}
        if discovery.get("include_in_sitemap") is True and isinstance(discovery.get("canonical_url"), str):
            expected[discovery["canonical_url"]] = discovery.get("lastmod")
    for missing in sorted(set(expected) - set(entries)):
        _finding(findings, "XS_MANIFEST_URL_MISSING", str(paths[0]), f"manifest sitemap URL is missing: {missing}")
    for extra in sorted(set(entries) - set(expected)):
        _finding(findings, "XS_MANIFEST_URL_EXTRA", str(paths[0]), f"URL is not approved by the manifest: {extra}")
    for loc in sorted(set(entries) & set(expected)):
        if expected[loc] is not None and entries[loc] != expected[loc]:
            _finding(findings, "XS_LASTMOD_MISMATCH", str(paths[0]), f"lastmod for {loc!r} must equal the manifest value {expected[loc]!r}")
    return findings


def validate_files(manifest_path: Path, plan_path: Path, sitemap_paths: list[Path] | None = None) -> list[Finding]:
    manifest, manifest_raw = _load_json(manifest_path)
    plan, _ = _load_json(plan_path)
    manifest_findings, routes_by_id, approved_origins = validate_manifest(manifest)
    findings = list(manifest_findings)
    findings.extend(validate_wireframe(plan, manifest, manifest_raw, routes_by_id))
    if sitemap_paths:
        findings.extend(validate_sitemaps(sitemap_paths, manifest, approved_origins))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--sitemap", action="append", default=[], type=Path, help="First path is urlset or sitemapindex; repeat for local child files.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")
    args = parser.parse_args()
    try:
        findings = validate_files(args.manifest, args.plan, args.sitemap)
    except SitePlanInputError as error:
        findings = [Finding("INPUT_INVALID", "P0", "$", str(error))]
    if args.json:
        print(json.dumps({"valid": not findings, "finding_count": len(findings), "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"{item.severity} {item.code} {item.path}: {item.message}", file=sys.stderr)
    else:
        print("site plan valid: manifest, wireframe, and sitemap contracts passed")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
