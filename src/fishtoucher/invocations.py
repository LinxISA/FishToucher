"""Provider-neutral invocation receipts and immutable request/response logs."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from .contracts import (
    CONTRACT,
    is_integer,
    is_non_empty_string,
    is_sha256,
    is_slug,
    is_utc_timestamp,
    require_exact_fields,
    validate_string_list,
)

RECEIPT_FIELDS = {
    "contract",
    "kind",
    "invocation_id",
    "run_id",
    "assignment_id",
    "actor",
    "driver",
    "request_log",
    "response_log",
    "request_sha256",
    "response_sha256",
    "started_at",
    "ended_at",
    "status",
    "exit_code",
    "usage",
    "tool_actions",
}


def invocation_log_names(name: str, role_id: str) -> tuple[str, str]:
    if not is_slug(name) or not is_slug(role_id):
        raise ValueError("name and role_id must be short kebab-case strings")
    return f"{name}-{role_id}-req.json", f"{name}-{role_id}-resp.json"


def _canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_invocation_logs(
    directory: str | Path,
    name: str,
    role_id: str,
    request: Any,
    response: Any,
) -> dict[str, str]:
    """Write mode-0600, create-once logs and return their names and hashes."""

    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    request_name, response_name = invocation_log_names(name, role_id)
    values = ((request_name, request), (response_name, response))
    hashes: dict[str, str] = {}
    for filename, value in values:
        data = _canonical_json(value)
        path = root / filename
        with path.open("xb") as stream:
            stream.write(data)
        os.chmod(path, 0o600)
        hashes[filename] = hashlib.sha256(data).hexdigest()
    return {
        "request_log": request_name,
        "response_log": response_name,
        "request_sha256": hashes[request_name],
        "response_sha256": hashes[response_name],
    }


def validate_invocation_receipt(data: Any) -> list[str]:
    """Return structural and semantic violations in an invocation receipt."""

    if not isinstance(data, dict):
        return ["receipt must be an object"]
    errors = require_exact_fields(data, RECEIPT_FIELDS, "receipt")
    if data.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT!r}")
    if data.get("kind") != "invocation":
        errors.append("kind must be 'invocation'")
    for field in ("invocation_id", "run_id", "assignment_id"):
        if not is_non_empty_string(data.get(field)):
            errors.append(f"{field} must be a non-empty string")

    actor = data.get("actor")
    errors.extend(require_exact_fields(actor, {"name", "role_id"}, "actor"))
    if isinstance(actor, dict):
        for field in ("name", "role_id"):
            if not is_slug(actor.get(field)):
                errors.append(f"actor.{field} must be short kebab-case")
    driver = data.get("driver")
    driver_fields = {"id", "kind", "provider", "model"}
    errors.extend(require_exact_fields(driver, driver_fields, "driver"))
    if isinstance(driver, dict):
        for field in driver_fields:
            if not is_non_empty_string(driver.get(field)):
                errors.append(f"driver.{field} must be a non-empty string")

    if (
        isinstance(actor, dict)
        and is_slug(actor.get("name"))
        and is_slug(actor.get("role_id"))
    ):
        expected = invocation_log_names(actor["name"], actor["role_id"])
        if data.get("request_log") != expected[0]:
            errors.append(f"request_log must be {expected[0]!r}")
        if data.get("response_log") != expected[1]:
            errors.append(f"response_log must be {expected[1]!r}")
    for field in ("request_sha256", "response_sha256"):
        if not is_sha256(data.get(field)):
            errors.append(f"{field} must be a lowercase SHA-256")
    for field in ("started_at", "ended_at"):
        if not is_utc_timestamp(data.get(field)):
            errors.append(f"{field} must be a valid UTC timestamp")
    if is_utc_timestamp(data.get("started_at")) and is_utc_timestamp(
        data.get("ended_at")
    ):
        started = datetime.fromisoformat(data["started_at"][:-1] + "+00:00")
        ended = datetime.fromisoformat(data["ended_at"][:-1] + "+00:00")
        if ended < started:
            errors.append("ended_at must not precede started_at")
    status = data.get("status")
    if status not in {"success", "failure", "interrupted"}:
        errors.append("status must be success, failure, or interrupted")
    exit_code = data.get("exit_code")
    if not is_integer(exit_code):
        errors.append("exit_code must be an integer")
    elif status == "success" and exit_code != 0:
        errors.append("successful invocation requires exit_code 0")
    elif status in {"failure", "interrupted"} and exit_code == 0:
        errors.append("unsuccessful invocation requires non-zero exit_code")
    usage = data.get("usage")
    errors.extend(
        require_exact_fields(usage, {"input_tokens", "output_tokens"}, "usage")
    )
    if isinstance(usage, dict):
        for field in ("input_tokens", "output_tokens"):
            if not is_integer(usage.get(field)) or usage[field] < 0:
                errors.append(f"usage.{field} must be a non-negative integer")
    errors.extend(validate_string_list(data.get("tool_actions"), "tool_actions"))
    return errors
