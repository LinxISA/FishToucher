"""Dependency-free validation for FishToucher agent messages and mailboxes."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "fishtoucher.message/v1"
MESSAGE_KINDS = {
    "observation",
    "work_packet",
    "ack",
    "question",
    "answer",
    "result",
    "verdict",
    "feedback",
    "escalation",
}
REPLY_REQUIRED_KINDS = MESSAGE_KINDS - {"observation", "escalation"}
ENVELOPE_FIELDS = {
    "protocol",
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
SENDER_FIELDS = {"role", "provider", "model"}
UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


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


def _validate_kind_payload(kind: Any, payload: dict[str, Any], errors: list[str]) -> None:
    requirements: dict[str, dict[str, type]] = {
        "work_packet": {
            "write_scope": list,
            "acceptance": list,
            "budget": dict,
        },
        "result": {
            "status": str,
            "changed_files": list,
            "commands": list,
        },
        "verdict": {
            "disposition": str,
            "evidence_checked": list,
        },
    }
    kind_requirements = requirements.get(kind, {}) if isinstance(kind, str) else {}
    for field, expected_type in kind_requirements.items():
        if field not in payload:
            errors.append(f"missing payload.{field} for {kind}")
        elif not isinstance(payload[field], expected_type):
            errors.append(
                f"payload.{field} for {kind} must be a {expected_type.__name__}"
            )

    if kind == "verdict":
        disposition = payload.get("disposition")
        if not isinstance(disposition, str) or disposition not in {
            "accept",
            "reject",
            "escalate",
        }:
            errors.append("payload.disposition must be accept, reject, or escalate")


def validate_message(message: Any) -> list[str]:
    """Return structural violations in one ``fishtoucher.message/v1`` message."""

    if not isinstance(message, dict):
        return ["message must be an object"]

    errors: list[str] = []
    missing = ENVELOPE_FIELDS - message.keys()
    unexpected = message.keys() - ENVELOPE_FIELDS
    for field in sorted(missing):
        errors.append(f"missing message field: {field}")
    if unexpected:
        errors.append("unexpected message fields: " + ", ".join(sorted(unexpected)))

    if message.get("protocol") != PROTOCOL:
        errors.append(f"protocol must be {PROTOCOL!r}")
    for field in ("message_id", "run_id"):
        if not _is_non_empty_string(message.get(field)):
            errors.append(f"{field} must be a non-empty string")

    sequence = message.get("sequence")
    if not _is_integer(sequence) or sequence < 1:
        errors.append("sequence must be an integer greater than or equal to 1")

    kind = message.get("kind")
    if not isinstance(kind, str) or kind not in MESSAGE_KINDS:
        errors.append("kind must be one of: " + ", ".join(sorted(MESSAGE_KINDS)))

    sender = message.get("sender")
    if not isinstance(sender, dict):
        errors.append("sender must be an object")
    else:
        missing_sender = SENDER_FIELDS - sender.keys()
        unexpected_sender = sender.keys() - SENDER_FIELDS
        for field in sorted(missing_sender):
            errors.append(f"missing sender.{field}")
        if unexpected_sender:
            errors.append(
                "unexpected sender fields: " + ", ".join(sorted(unexpected_sender))
            )
        for field in sorted(SENDER_FIELDS):
            if field in sender and not _is_non_empty_string(sender[field]):
                errors.append(f"sender.{field} must be a non-empty string")

    recipients = message.get("recipients")
    if not isinstance(recipients, list) or not recipients:
        errors.append("recipients must be a non-empty array")
    else:
        if any(not _is_non_empty_string(recipient) for recipient in recipients):
            errors.append("every recipient must be a non-empty string")
        string_recipients = [item for item in recipients if isinstance(item, str)]
        if len(set(string_recipients)) != len(string_recipients):
            errors.append("recipients must be unique")

    in_reply_to = message.get("in_reply_to")
    if in_reply_to is not None and not _is_non_empty_string(in_reply_to):
        errors.append("in_reply_to must be null or a non-empty string")
    if (
        isinstance(kind, str)
        and kind in REPLY_REQUIRED_KINDS
        and not _is_non_empty_string(in_reply_to)
    ):
        errors.append(f"{kind} requires in_reply_to to name an earlier message")

    if not _validate_timestamp(message.get("created_at")):
        errors.append("created_at must be a valid UTC timestamp ending in Z")

    payload = message.get("payload")
    if not isinstance(payload, dict):
        errors.append("payload must be an object")
    else:
        if not _is_non_empty_string(payload.get("summary")):
            errors.append("payload.summary must be a non-empty string")
        for field in ("artifacts", "claims", "requests"):
            if field in payload and not isinstance(payload[field], list):
                errors.append(f"payload.{field} must be an array")
        _validate_kind_payload(kind, payload, errors)

    return errors


def load_mailbox(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSON Lines mailbox, preserving its on-disk ordering."""

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


def _sender_identity(message: dict[str, Any]) -> tuple[Any, Any, Any] | None:
    sender = message.get("sender")
    if not isinstance(sender, dict):
        return None
    return sender.get("role"), sender.get("provider"), sender.get("model")


def validate_mailbox(messages: Iterable[Any]) -> list[str]:
    """Return envelope and reply-graph violations for an ordered mailbox."""

    mailbox = list(messages)
    errors: list[str] = []
    if not mailbox:
        return ["mailbox must contain at least one message"]

    positions: dict[str, int] = {}
    for index, message in enumerate(mailbox, start=1):
        for error in validate_message(message):
            errors.append(f"message {index}: {error}")
        if not isinstance(message, dict):
            continue
        message_id = message.get("message_id")
        if isinstance(message_id, str):
            if message_id in positions:
                errors.append(f"message {index}: duplicate message_id {message_id!r}")
            else:
                positions[message_id] = index

    expected_run_id: Any = None
    for index, message in enumerate(mailbox, start=1):
        if not isinstance(message, dict):
            continue

        if message.get("sequence") != index:
            errors.append(f"message {index}: sequence must be {index}")

        run_id = message.get("run_id")
        if index == 1:
            expected_run_id = run_id
        elif run_id != expected_run_id:
            errors.append(
                f"message {index}: run_id must match the first mailbox message"
            )

        reply_id = message.get("in_reply_to")
        if not isinstance(reply_id, str):
            continue
        reply_position = positions.get(reply_id)
        if reply_position is None:
            errors.append(
                f"message {index}: in_reply_to references unknown message {reply_id!r}"
            )
            continue
        if reply_position >= index:
            errors.append(
                f"message {index}: in_reply_to must reference an earlier message"
            )
            continue

        if message.get("kind") != "verdict":
            continue
        result = mailbox[reply_position - 1]
        if not isinstance(result, dict) or result.get("kind") != "result":
            errors.append(f"message {index}: verdict must reply to a result")
        elif _sender_identity(message) == _sender_identity(result):
            errors.append(
                f"message {index}: implementer cannot self-verify its result"
            )

    return errors
