"""Invocation receipt validator for fishtoucher.invocation/v1."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

PROTOCOL = "fishtoucher.invocation/v1"

ALLOWED_FIELDS = frozenset({
    "invocation",
    "run",
    "packet",
    "role",
    "provider",
    "model",
    "transport",
    "coordinator",
    "request_sha256",
    "response_sha256",
    "started_at",
    "ended_at",
    "status",
    "exit_code",
    "protocol",
})

SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _validate_identity(value: Any, label: str) -> list[str]:
    """Validate an identity object {role, provider, model}."""
    errors: list[str] = []
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return errors
    allowed = {"role", "provider", "model"}
    actual = set(value.keys())
    if actual != allowed:
        extra = actual - allowed
        missing = allowed - actual
        if extra:
            errors.append(
                f"{label} contains unknown field(s): {', '.join(sorted(extra))}"
            )
        if missing:
            errors.append(
                f"{label} missing required field(s): {', '.join(sorted(missing))}"
            )
        return errors
    for field in ("role", "provider", "model"):
        if not _is_non_empty_string(value[field]):
            errors.append(f"{label}.{field} must be a non-empty string")
    return errors


def validate_invocation_receipt(data: dict[str, Any]) -> list[str]:
    """Validate a fishtoucher.invocation/v1 receipt.

    Returns a list of error messages, empty when valid.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["receipt must be a JSON object"]

    actual_keys = set(data.keys())
    unknown = actual_keys - ALLOWED_FIELDS
    if unknown:
        for field in sorted(unknown):
            errors.append(f"unknown field: {field}")

    missing = ALLOWED_FIELDS - actual_keys
    if missing:
        for field in sorted(missing):
            errors.append(f"missing required field: {field}")

    # simple string identities
    for field in ("invocation", "run", "packet", "role", "provider", "model"):
        if field in data:
            if not _is_non_empty_string(data[field]):
                errors.append(f"{field} must be a non-empty string")

    if "protocol" in data and data["protocol"] != PROTOCOL:
        errors.append(
            f"invalid protocol: {data['protocol']!r}, expected {PROTOCOL!r}"
        )

    # SHA-256 digests
    for field in ("request_sha256", "response_sha256"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or SHA256_PATTERN.fullmatch(value) is None:
                errors.append(f"{field} must be a 64-character hex string")

    # timestamps
    for field in ("started_at", "ended_at"):
        if field in data:
            if not _validate_timestamp(data[field]):
                errors.append(f"{field} must be a valid UTC timestamp (ISO 8601 ending in Z)")

    # status
    if "status" in data:
        status = data["status"]
        if status not in ("success", "failure"):
            errors.append("status must be 'success' or 'failure'")

    # exit_code
    if "exit_code" in data:
        exit_code = data["exit_code"]
        if not _is_integer(exit_code):
            errors.append("exit_code must be an integer (not boolean)")

    # semantic consistency
    if "status" in data and "exit_code" in data:
        status = data["status"]
        exit_code = data["exit_code"]
        if _is_integer(exit_code):
            if status == "success" and exit_code != 0:
                errors.append("exit_code must be 0 when status is 'success'")
            if status == "failure" and exit_code == 0:
                errors.append("exit_code must not be 0 when status is 'failure'")

    # temporal ordering
    if "started_at" in data and "ended_at" in data:
        if _validate_timestamp(data["started_at"]) and _validate_timestamp(data["ended_at"]):
            started = datetime.fromisoformat(data["started_at"][:-1] + "+00:00")
            ended = datetime.fromisoformat(data["ended_at"][:-1] + "+00:00")
            if ended < started:
                errors.append("ended_at must not precede started_at")

    # identity sub-objects
    if "transport" in data:
        errors.extend(_validate_identity(data["transport"], "transport"))
    if "coordinator" in data:
        errors.extend(_validate_identity(data["coordinator"], "coordinator"))

    return errors
