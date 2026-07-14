#!/usr/bin/env python3
"""Validate evaluator-owned cross-product schema/coverage fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT_KEYS = {
    "schema_version",
    "case_set_id",
    "fixture_status",
    "model_results_included",
    "purpose",
    "required_locales",
    "claim_boundary",
    "cases",
}
CASE_KEYS = {
    "case_id",
    "locale",
    "surface_type",
    "audience",
    "primary_task",
    "expected_representation",
    "brand_evidence_boundary",
    "mobile_transformation",
    "hidden_acceptance_focus",
}
BRAND_KEYS = {"allowed_sources", "must_not_infer", "ethics_constraints"}
MOBILE_KEYS = {"desktop_context", "changes", "must_preserve"}
CLAIM_KEYS = {"validates", "does_not_validate"}
EXPECTED_CASE_IDS = {
    "b2b-audit-log",
    "medical-appointment",
    "api-key-management",
    "cart-return-subscription",
    "editorial-archive",
    "collaboration-inbox",
    "preferences-settings",
    "brand-system-campaign",
}
ALLOWED_LOCALES = {"zh-Hant", "en"}
ALLOWED_SURFACES = {
    "data_table",
    "form_flow",
    "settings",
    "commerce",
    "editorial",
    "collaboration",
    "design_system",
}
REQUIRED_NON_CLAIMS = {
    "model_quality",
    "case_execution",
    "skill_activation",
    "reference_routing",
    "browser_behavior",
    "wcag_conformance",
}
CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProductCaseError(ValueError):
    """Raised when product coverage fixtures are malformed or overclaim results."""


def load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ProductCaseError(f"refusing symlink fixture: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProductCaseError(f"cannot read valid JSON fixture: {error}") from error
    if not isinstance(value, dict):
        raise ProductCaseError("fixture root must be an object")
    return value


def require_string(value: object, label: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise ProductCaseError(f"{label} must be a non-empty string")
    return value


def require_string_list(value: object, label: str, minimum: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ProductCaseError(f"{label} must contain at least {minimum} strings")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ProductCaseError(f"{label} must contain only non-empty strings")
    if len(value) != len(set(value)):
        raise ProductCaseError(f"{label} contains duplicates")
    return value


def require_exact_keys(value: object, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ProductCaseError(f"{label} must contain exactly {sorted(expected)}")
    return value


def validate(path: Path) -> int:
    data = load_json(path)
    require_exact_keys(data, ROOT_KEYS, "fixture root")
    if data["schema_version"] != 1:
        raise ProductCaseError("schema_version must equal 1")
    if data["case_set_id"] != "wow-cross-product-non-landing-v1":
        raise ProductCaseError("case_set_id must remain wow-cross-product-non-landing-v1")
    if data["fixture_status"] != "schema_coverage_only":
        raise ProductCaseError("fixture_status must remain schema_coverage_only")
    if data["model_results_included"] is not False:
        raise ProductCaseError("product case fixtures must not include model results")
    require_string(data["purpose"], "purpose", 40)

    required_locales = set(require_string_list(data["required_locales"], "required_locales", 2))
    if required_locales != ALLOWED_LOCALES:
        raise ProductCaseError("required_locales must contain exactly zh-Hant and en")

    claims = require_exact_keys(data["claim_boundary"], CLAIM_KEYS, "claim_boundary")
    validates = set(require_string_list(claims["validates"], "claim_boundary.validates"))
    if validates != {"fixture_schema", "case_coverage", "locale_distribution"}:
        raise ProductCaseError("claim_boundary.validates exceeds schema/coverage scope")
    non_claims = set(require_string_list(claims["does_not_validate"], "claim_boundary.does_not_validate"))
    if not REQUIRED_NON_CLAIMS.issubset(non_claims):
        raise ProductCaseError("claim_boundary must reject execution, model, routing, browser, and WCAG claims")

    cases = data["cases"]
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASE_IDS):
        raise ProductCaseError(f"cases must contain exactly {len(EXPECTED_CASE_IDS)} definitions")

    case_ids: set[str] = set()
    locales: set[str] = set()
    for index, raw_case in enumerate(cases):
        label = f"cases[{index}]"
        case = require_exact_keys(raw_case, CASE_KEYS, label)

        case_id = require_string(case["case_id"], f"{label}.case_id")
        if not CASE_ID_PATTERN.fullmatch(case_id) or case_id in case_ids:
            raise ProductCaseError(f"{label}.case_id must be unique kebab-case")
        case_ids.add(case_id)

        locale = case["locale"]
        if locale not in ALLOWED_LOCALES:
            raise ProductCaseError(f"{label}.locale must be zh-Hant or en")
        locales.add(locale)

        if case["surface_type"] not in ALLOWED_SURFACES:
            raise ProductCaseError(f"{label}.surface_type is not an allowed non-landing product surface")
        require_string(case["audience"], f"{label}.audience", 12)
        require_string(case["primary_task"], f"{label}.primary_task", 12)
        require_string_list(case["expected_representation"], f"{label}.expected_representation", 2)
        require_string_list(case["hidden_acceptance_focus"], f"{label}.hidden_acceptance_focus", 3)

        brand = require_exact_keys(case["brand_evidence_boundary"], BRAND_KEYS, f"{label}.brand_evidence_boundary")
        for key in BRAND_KEYS:
            require_string_list(brand[key], f"{label}.brand_evidence_boundary.{key}")

        mobile = require_exact_keys(case["mobile_transformation"], MOBILE_KEYS, f"{label}.mobile_transformation")
        require_string(mobile["desktop_context"], f"{label}.mobile_transformation.desktop_context", 12)
        require_string_list(mobile["changes"], f"{label}.mobile_transformation.changes")
        require_string_list(mobile["must_preserve"], f"{label}.mobile_transformation.must_preserve")

    if case_ids != EXPECTED_CASE_IDS:
        missing = sorted(EXPECTED_CASE_IDS - case_ids)
        unexpected = sorted(case_ids - EXPECTED_CASE_IDS)
        raise ProductCaseError(f"fixed case IDs changed; missing={missing}, unexpected={unexpected}")
    if not required_locales.issubset(locales):
        raise ProductCaseError("cases must distribute coverage across zh-Hant and en")
    return len(cases)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        count = validate(args.fixture.expanduser())
    except ProductCaseError as error:
        print(f"product case fixture invalid: {error}", file=sys.stderr)
        return 1
    print(f"product case fixture valid: {count} definition-only cases; no model results validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
