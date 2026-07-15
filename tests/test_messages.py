from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishtoucher.cli import main  # noqa: E402
from fishtoucher.messages import (  # noqa: E402
    load_mailbox,
    validate_mailbox,
    validate_message,
)


def message(
    sequence: int,
    kind: str,
    sender_role: str,
    *,
    in_reply_to: str | None = None,
) -> dict:
    message_id = f"run-001-{kind}-{sequence}"
    payload: dict = {"summary": f"{kind} message"}
    if kind == "work_packet":
        payload.update(
            write_scope=["src/fishtoucher/messages.py"],
            acceptance=["message validation passes"],
            budget={"max_changed_files": 1},
        )
    elif kind == "result":
        payload.update(status="pass", changed_files=[], commands=[])
    elif kind == "verdict":
        payload.update(disposition="accept", evidence_checked=[])
    return {
        "protocol": "fishtoucher.message/v1",
        "message_id": message_id,
        "run_id": "run-001",
        "sequence": sequence,
        "kind": kind,
        "sender": {
            "role": sender_role,
            "provider": "openai" if sender_role != "deepseek_executor" else "deepseek",
            "model": "test-model",
        },
        "recipients": ["coordinator"],
        "in_reply_to": in_reply_to,
        "created_at": "2026-07-15T10:00:00Z",
        "payload": payload,
    }


def valid_chain() -> list[dict]:
    observation = message(1, "observation", "gpt_sensor")
    packet = message(
        2,
        "work_packet",
        "gpt_sensor",
        in_reply_to=observation["message_id"],
    )
    ack = message(
        3,
        "ack",
        "deepseek_executor",
        in_reply_to=packet["message_id"],
    )
    result = message(
        4,
        "result",
        "deepseek_executor",
        in_reply_to=packet["message_id"],
    )
    verdict = message(
        5,
        "verdict",
        "gpt_verifier",
        in_reply_to=result["message_id"],
    )
    return [observation, packet, ack, result, verdict]


class MessageValidationTests(unittest.TestCase):
    def test_valid_work_packet(self) -> None:
        self.assertEqual(validate_message(valid_chain()[1]), [])

    def test_envelope_and_kind_specific_fields_are_required(self) -> None:
        broken = message(1, "result", "deepseek_executor")
        del broken["sender"]["model"]
        del broken["payload"]["commands"]
        errors = validate_message(broken)
        self.assertTrue(any("sender.model" in error for error in errors))
        self.assertTrue(any("payload.commands" in error for error in errors))

    def test_timestamp_must_be_valid_utc(self) -> None:
        broken = message(1, "observation", "gpt_sensor")
        broken["created_at"] = "2026-02-30T10:00:00+08:00"
        self.assertTrue(any("UTC" in error for error in validate_message(broken)))

    def test_duplicate_recipients_are_rejected(self) -> None:
        broken = message(1, "observation", "gpt_sensor")
        broken["recipients"] = ["executor", "executor"]
        self.assertTrue(any("unique" in error for error in validate_message(broken)))

    def test_reply_bearing_kinds_require_parent_message(self) -> None:
        for kind in (
            "work_packet",
            "ack",
            "question",
            "answer",
            "result",
            "verdict",
            "feedback",
        ):
            with self.subTest(kind=kind):
                broken = message(1, kind, "deepseek_executor")
                errors = validate_message(broken)
                self.assertTrue(any("requires in_reply_to" in error for error in errors))


class MailboxValidationTests(unittest.TestCase):
    def test_valid_chain(self) -> None:
        self.assertEqual(validate_mailbox(valid_chain()), [])

    def test_sequence_must_be_contiguous_from_one(self) -> None:
        broken = valid_chain()
        broken[2]["sequence"] = 4
        self.assertTrue(any("sequence must be 3" in error for error in validate_mailbox(broken)))

    def test_duplicate_ids_are_rejected(self) -> None:
        broken = valid_chain()
        broken[1]["message_id"] = broken[0]["message_id"]
        self.assertTrue(any("duplicate message_id" in error for error in validate_mailbox(broken)))

    def test_forward_and_missing_reply_references_are_rejected(self) -> None:
        forward = valid_chain()
        forward[1]["in_reply_to"] = forward[3]["message_id"]
        self.assertTrue(any("earlier message" in error for error in validate_mailbox(forward)))

        missing = valid_chain()
        missing[1]["in_reply_to"] = "not-in-mailbox"
        self.assertTrue(any("unknown message" in error for error in validate_mailbox(missing)))

    def test_implementer_cannot_verify_own_result(self) -> None:
        broken = valid_chain()
        broken[-1]["sender"] = copy.deepcopy(broken[-2]["sender"])
        self.assertTrue(any("self-verify" in error for error in validate_mailbox(broken)))

    def test_verdict_must_reply_to_result(self) -> None:
        broken = valid_chain()
        broken[-1]["in_reply_to"] = broken[1]["message_id"]
        self.assertTrue(any("reply to a result" in error for error in validate_mailbox(broken)))

    def test_mailbox_loader_reports_bad_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mailbox.jsonl"
            path.write_text("{}\nnot-json\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_mailbox(path)


class MessageCliTests(unittest.TestCase):
    def test_message_and_mailbox_commands(self) -> None:
        chain = valid_chain()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            message_path = root / "message.json"
            mailbox_path = root / "mailbox.jsonl"
            message_path.write_text(json.dumps(chain[0]), encoding="utf-8")
            mailbox_path.write_text(
                "".join(json.dumps(item) + "\n" for item in chain),
                encoding="utf-8",
            )

            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["message", str(message_path)]), 0)
                self.assertEqual(main(["mailbox", str(mailbox_path)]), 0)
            self.assertEqual(output.getvalue().count("PASS"), 2)


if __name__ == "__main__":
    unittest.main()
