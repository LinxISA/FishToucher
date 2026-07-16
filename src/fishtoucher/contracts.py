"""Shared primitives for the FishToucher prototype contracts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

CONTRACT = "fishtoucher.prototype"
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,47}$")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_slug(value: Any) -> bool:
    return isinstance(value, str) and SLUG.fullmatch(value) is not None


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_HEX.fullmatch(value) is not None


def is_utc_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def require_exact_fields(
    value: Any,
    fields: set[str] | frozenset[str],
    label: str,
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    actual = set(value)
    for field in sorted(fields - actual):
        errors.append(f"{label} is missing: {field}")
    unexpected = actual - fields
    if unexpected:
        errors.append(
            f"{label} has unexpected fields: " + ", ".join(sorted(unexpected))
        )
    return errors


def validate_string_list(
    value: Any,
    label: str,
    *,
    non_empty: bool = False,
) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be an array"]
    errors: list[str] = []
    if non_empty and not value:
        errors.append(f"{label} must not be empty")
    if any(not is_non_empty_string(item) for item in value):
        errors.append(f"every {label} item must be a non-empty string")
    strings = [item for item in value if isinstance(item, str)]
    if len(strings) != len(set(strings)):
        errors.append(f"{label} items must be unique")
    return errors
