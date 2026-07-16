"""Compact assignment/result/verdict contracts and mailbox validation."""

from __future__ import annotations

import json
from collections.abc import Iterable
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
from .drivers import path_allowed

MESSAGE_KINDS = {"assignment", "result", "verdict", "escalation"}
REPLY_REQUIRED = {"result", "verdict", "escalation"}
ENVELOPE_FIELDS = {
    "contract",
    "message_id",
    "run_id",
    "sequence",
    "kind",
    "sender",
    "recipients",
    "in_reply_to",
    "created_at",
    "payload",
}
SENDER_FIELDS = {"name", "role_id", "driver_id", "model"}
ASSIGNMENT_FIELDS = {
    "summary",
    "assignee",
    "target",
    "base_revision",
    "authority",
    "protected_paths",
    "context_sections",
    "done_when",
    "required_commands",
    "budget",
    "escalate_when",
}
AUTHORITY_FIELDS = {"read", "write", "tools", "network", "delegate_roles"}
BUDGET_FIELDS = {
    "max_context_sections",
    "max_context_bytes",
    "max_delegated_calls",
}
BUDGET_LIMITS = {
    "max_context_sections": 8,
    "max_context_bytes": 32768,
    "max_delegated_calls": 4,
}
RESULT_FIELDS = {
    "summary",
    "status",
    "changed_files",
    "commands",
    "patch_sha256",
    "artifacts",
    "references",
    "delegated_invocations",
    "residual_risks",
}
VERDICT_FIELDS = {
    "summary",
    "disposition",
    "defects",
    "evidence_checked",
    "proof_boundary",
    "residual_risk",
}


def _validate_sender(sender: Any, errors: list[str]) -> None:
    errors.extend(require_exact_fields(sender, SENDER_FIELDS, "sender"))
    if not isinstance(sender, dict):
        return
    if not is_slug(sender.get("name")):
        errors.append("sender.name must be a short kebab-case name")
    if not is_slug(sender.get("role_id")):
        errors.append("sender.role_id must be a short kebab-case role")
    for field in ("driver_id", "model"):
        if not is_non_empty_string(sender.get(field)):
            errors.append(f"sender.{field} must be a non-empty string")


def _validate_context_sections(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("payload.context_sections must be a non-empty array")
        return
    fields = {"path", "start_line", "end_line", "purpose"}
    for index, section in enumerate(value):
        label = f"payload.context_sections[{index}]"
        errors.extend(require_exact_fields(section, fields, label))
        if not isinstance(section, dict):
            continue
        if not is_non_empty_string(section.get("path")):
            errors.append(f"{label}.path must be a non-empty string")
        if not is_non_empty_string(section.get("purpose")):
            errors.append(f"{label}.purpose must be a non-empty string")
        start = section.get("start_line")
        end = section.get("end_line")
        if not is_integer(start) or start < 1:
            errors.append(f"{label}.start_line must be positive")
        if not is_integer(end) or end < 1:
            errors.append(f"{label}.end_line must be positive")
        if is_integer(start) and is_integer(end) and end < start:
            errors.append(f"{label}.end_line must not precede start_line")


def _validate_budget(value: Any, section_count: int, errors: list[str]) -> None:
    errors.extend(require_exact_fields(value, BUDGET_FIELDS, "payload.budget"))
    if not isinstance(value, dict):
        return
    for field, maximum in BUDGET_LIMITS.items():
        item = value.get(field)
        minimum = 0 if field == "max_delegated_calls" else 1
        if not is_integer(item) or item < minimum:
            errors.append(f"payload.budget.{field} must be an integer >= {minimum}")
        elif item > maximum:
            errors.append(f"payload.budget.{field} must not exceed {maximum}")
    maximum_sections = value.get("max_context_sections")
    if is_integer(maximum_sections) and section_count > maximum_sections:
        errors.append("payload.context_sections exceeds max_context_sections")


def _validate_assignment(payload: dict[str, Any], errors: list[str]) -> None:
    errors.extend(require_exact_fields(payload, ASSIGNMENT_FIELDS, "payload"))
    assignee = payload.get("assignee")
    errors.extend(require_exact_fields(assignee, {"name", "role_id"}, "assignee"))
    if isinstance(assignee, dict):
        for field in ("name", "role_id"):
            if not is_slug(assignee.get(field)):
                errors.append(f"assignee.{field} must be short kebab-case")
    for field in ("summary", "target", "base_revision"):
        if not is_non_empty_string(payload.get(field)):
            errors.append(f"payload.{field} must be a non-empty string")

    authority = payload.get("authority")
    errors.extend(
        require_exact_fields(authority, AUTHORITY_FIELDS, "payload.authority")
    )
    if isinstance(authority, dict):
        for field in ("read", "write", "tools", "delegate_roles"):
            errors.extend(
                validate_string_list(
                    authority.get(field),
                    f"payload.authority.{field}",
                    non_empty=field in {"read", "tools"},
                )
            )
        if not isinstance(authority.get("network"), bool):
            errors.append("payload.authority.network must be boolean")
    for field, non_empty in (
        ("protected_paths", False),
        ("done_when", True),
        ("required_commands", True),
        ("escalate_when", True),
    ):
        errors.extend(
            validate_string_list(
                payload.get(field), f"payload.{field}", non_empty=non_empty
            )
        )
    sections = payload.get("context_sections")
    _validate_context_sections(sections, errors)
    _validate_budget(
        payload.get("budget"),
        len(sections) if isinstance(sections, list) else 0,
        errors,
    )


def _validate_artifacts(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("payload.artifacts must be an array")
        return
    for index, artifact in enumerate(value):
        label = f"payload.artifacts[{index}]"
        errors.extend(require_exact_fields(artifact, {"path", "sha256"}, label))
        if not isinstance(artifact, dict):
            continue
        if not is_non_empty_string(artifact.get("path")):
            errors.append(f"{label}.path must be a non-empty string")
        if not is_sha256(artifact.get("sha256")):
            errors.append(f"{label}.sha256 must be a lowercase SHA-256")


def _validate_delegated_invocations(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("payload.delegated_invocations must be an array")
        return
    fields = {
        "name",
        "role_id",
        "driver_id",
        "request_log",
        "response_log",
        "request_sha256",
        "response_sha256",
        "status",
    }
    for index, call in enumerate(value):
        label = f"payload.delegated_invocations[{index}]"
        errors.extend(require_exact_fields(call, fields, label))
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        role_id = call.get("role_id")
        if not is_slug(name):
            errors.append(f"{label}.name must be short kebab-case")
        if not is_slug(role_id):
            errors.append(f"{label}.role_id must be short kebab-case")
        if not is_non_empty_string(call.get("driver_id")):
            errors.append(f"{label}.driver_id must be non-empty")
        if is_slug(name) and is_slug(role_id):
            expected_request = f"{name}-{role_id}-req.json"
            expected_response = f"{name}-{role_id}-resp.json"
            if call.get("request_log") != expected_request:
                errors.append(f"{label}.request_log must be {expected_request!r}")
            if call.get("response_log") != expected_response:
                errors.append(f"{label}.response_log must be {expected_response!r}")
        for field in ("request_sha256", "response_sha256"):
            if not is_sha256(call.get(field)):
                errors.append(f"{label}.{field} must be a lowercase SHA-256")
        if call.get("status") not in {"success", "failure", "interrupted"}:
            errors.append(f"{label}.status is invalid")


def _validate_result(payload: dict[str, Any], errors: list[str]) -> None:
    errors.extend(require_exact_fields(payload, RESULT_FIELDS, "payload"))
    if not is_non_empty_string(payload.get("summary")):
        errors.append("payload.summary must be a non-empty string")
    status = payload.get("status")
    if status not in {"completed", "blocked", "failed"}:
        errors.append("payload.status must be completed, blocked, or failed")
    for field in ("changed_files", "commands", "references", "residual_risks"):
        errors.extend(validate_string_list(payload.get(field), f"payload.{field}"))
    patch_sha = payload.get("patch_sha256")
    if patch_sha is not None and not is_sha256(patch_sha):
        errors.append("payload.patch_sha256 must be null or a lowercase SHA-256")
    if status == "completed" and payload.get("changed_files") and patch_sha is None:
        errors.append("completed changed work requires payload.patch_sha256")
    _validate_artifacts(payload.get("artifacts"), errors)
    _validate_delegated_invocations(payload.get("delegated_invocations"), errors)


def _validate_defects(value: Any, disposition: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("payload.defects must be an array")
        return
    if disposition == "reject" and not value:
        errors.append("reject verdict requires at least one concrete defect")
    fields = {
        "id",
        "severity",
        "evidence",
        "required_fix",
        "write_scope",
        "required_commands",
    }
    for index, defect in enumerate(value):
        label = f"payload.defects[{index}]"
        errors.extend(require_exact_fields(defect, fields, label))
        if not isinstance(defect, dict):
            continue
        if not is_slug(defect.get("id")):
            errors.append(f"{label}.id must be short kebab-case")
        if defect.get("severity") not in {"critical", "high", "medium", "low"}:
            errors.append(f"{label}.severity is invalid")
        for field in ("evidence", "required_fix"):
            if not is_non_empty_string(defect.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        for field in ("write_scope", "required_commands"):
            errors.extend(
                validate_string_list(
                    defect.get(field), f"{label}.{field}", non_empty=True
                )
            )


def _validate_verdict(payload: dict[str, Any], errors: list[str]) -> None:
    errors.extend(require_exact_fields(payload, VERDICT_FIELDS, "payload"))
    if not is_non_empty_string(payload.get("summary")):
        errors.append("payload.summary must be a non-empty string")
    disposition = payload.get("disposition")
    if disposition not in {"accept", "reject", "escalate"}:
        errors.append("payload.disposition must be accept, reject, or escalate")
    _validate_defects(payload.get("defects"), disposition, errors)
    if disposition == "accept" and payload.get("defects"):
        errors.append("accept verdict cannot contain defects")
    for field in ("evidence_checked", "proof_boundary"):
        errors.extend(
            validate_string_list(payload.get(field), f"payload.{field}", non_empty=True)
        )
    if not is_non_empty_string(payload.get("residual_risk")):
        errors.append("payload.residual_risk must be a non-empty string")


def _validate_escalation(payload: dict[str, Any], errors: list[str]) -> None:
    fields = {"summary", "reason", "required_human_action", "evidence"}
    errors.extend(require_exact_fields(payload, fields, "payload"))
    for field in ("summary", "reason", "required_human_action"):
        if not is_non_empty_string(payload.get(field)):
            errors.append(f"payload.{field} must be a non-empty string")
    errors.extend(
        validate_string_list(
            payload.get("evidence"), "payload.evidence", non_empty=True
        )
    )


def validate_message(message: Any) -> list[str]:
    """Return structural violations in one prototype message."""

    if not isinstance(message, dict):
        return ["message must be an object"]
    errors = require_exact_fields(message, ENVELOPE_FIELDS, "message")
    if message.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT!r}")
    for field in ("message_id", "run_id"):
        if not is_non_empty_string(message.get(field)):
            errors.append(f"{field} must be a non-empty string")
    sequence = message.get("sequence")
    if not is_integer(sequence) or sequence < 1:
        errors.append("sequence must be an integer >= 1")
    kind = message.get("kind")
    if kind not in MESSAGE_KINDS:
        errors.append("kind must be assignment, result, verdict, or escalation")
    _validate_sender(message.get("sender"), errors)
    errors.extend(
        validate_string_list(message.get("recipients"), "recipients", non_empty=True)
    )
    parent = message.get("in_reply_to")
    if parent is not None and not is_non_empty_string(parent):
        errors.append("in_reply_to must be null or a non-empty string")
    if kind in REPLY_REQUIRED and not is_non_empty_string(parent):
        errors.append(f"{kind} requires in_reply_to")
    if not is_utc_timestamp(message.get("created_at")):
        errors.append("created_at must be a valid UTC timestamp ending in Z")
    payload = message.get("payload")
    if not isinstance(payload, dict):
        errors.append("payload must be an object")
    elif kind == "assignment":
        _validate_assignment(payload, errors)
    elif kind == "result":
        _validate_result(payload, errors)
    elif kind == "verdict":
        _validate_verdict(payload, errors)
    elif kind == "escalation":
        _validate_escalation(payload, errors)
    return errors


def load_mailbox(path: str | Path) -> list[dict[str, Any]]:
    """Read an ordered JSONL mailbox."""

    mailbox: list[dict[str, Any]] = []
    mailbox_path = Path(path)
    with mailbox_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise ValueError(f"{mailbox_path}: line {line_number} is blank")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{mailbox_path}: line {line_number}: {error.msg}"
                ) from error
            if not isinstance(value, dict):
                raise ValueError(
                    f"{mailbox_path}: line {line_number} must contain an object"
                )
            mailbox.append(value)
    return mailbox


def validate_mailbox(messages: Iterable[Any]) -> list[str]:
    """Validate ordering, reply graph, scope, delegation, and reviewer independence."""

    mailbox = list(messages)
    if not mailbox:
        return ["mailbox must contain at least one message"]
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    first_run: Any = None
    for index, message in enumerate(mailbox, start=1):
        errors.extend(
            f"message {index}: {error}" for error in validate_message(message)
        )
        if not isinstance(message, dict):
            continue
        if message.get("sequence") != index:
            errors.append(f"message {index}: sequence must be {index}")
        if first_run is None:
            first_run = message.get("run_id")
        elif message.get("run_id") != first_run:
            errors.append(f"message {index}: run_id must match the mailbox")
        message_id = message.get("message_id")
        if isinstance(message_id, str):
            if message_id in by_id:
                errors.append(f"message {index}: duplicate message_id {message_id!r}")
            else:
                by_id[message_id] = message

        parent_id = message.get("in_reply_to")
        if parent_id is None:
            continue
        parent = by_id.get(parent_id)
        if parent is None or parent is message:
            errors.append(f"message {index}: reply must reference an earlier message")
            continue
        kind = message.get("kind")
        if kind == "result" and parent.get("kind") != "assignment":
            errors.append(f"message {index}: result must reply to an assignment")
        if kind == "verdict" and parent.get("kind") != "result":
            errors.append(f"message {index}: verdict must reply to a result")
        if kind == "result" and parent.get("kind") == "assignment":
            parent_payload = parent.get("payload")
            result_payload = message.get("payload")
            sender_value = message.get("sender")
            if not isinstance(parent_payload, dict) or not isinstance(
                result_payload, dict
            ):
                continue
            assignee_value = parent_payload.get("assignee")
            assignee = assignee_value if isinstance(assignee_value, dict) else {}
            sender = sender_value if isinstance(sender_value, dict) else {}
            if sender.get("name") != assignee.get("name") or sender.get(
                "role_id"
            ) != assignee.get("role_id"):
                errors.append(f"message {index}: result sender must match assignee")
            authority_value = parent_payload.get("authority")
            authority = authority_value if isinstance(authority_value, dict) else {}
            write_scope = authority.get("write", [])
            changed_files = result_payload.get("changed_files", [])
            for path in changed_files if isinstance(changed_files, list) else []:
                if (
                    isinstance(path, str)
                    and isinstance(write_scope, list)
                    and not path_allowed(path, write_scope)
                ):
                    errors.append(
                        f"message {index}: changed file {path!r} is outside write scope"
                    )
            calls = result_payload.get("delegated_invocations", [])
            budget_value = parent_payload.get("budget")
            budget = budget_value if isinstance(budget_value, dict) else {}
            maximum = budget.get("max_delegated_calls")
            if is_integer(maximum) and isinstance(calls, list) and len(calls) > maximum:
                errors.append(
                    f"message {index}: delegated invocations exceed packet budget"
                )
            raw_allowed_roles = authority.get("delegate_roles", [])
            allowed_roles = (
                {role for role in raw_allowed_roles if isinstance(role, str)}
                if isinstance(raw_allowed_roles, list)
                else set()
            )
            for call in calls if isinstance(calls, list) else []:
                if isinstance(call, dict) and call.get("role_id") not in allowed_roles:
                    errors.append(
                        f"message {index}: delegated role is outside assignment authority"
                    )
        if kind == "verdict" and parent.get("kind") == "result":
            sender = message.get("sender")
            parent_sender = parent.get("sender")
            sender_name = sender.get("name") if isinstance(sender, dict) else None
            parent_name = (
                parent_sender.get("name") if isinstance(parent_sender, dict) else None
            )
            if sender_name is not None and sender_name == parent_name:
                errors.append(f"message {index}: implementer cannot self-verify")
    return errors
