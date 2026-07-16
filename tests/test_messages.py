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
from fishtoucher.contracts import CONTRACT  # noqa: E402
from fishtoucher.messages import (  # noqa: E402
    load_mailbox,
    validate_mailbox,
    validate_message,
)


def _envelope(
    sequence: int,
    kind: str,
    name: str,
    role_id: str,
    payload: dict,
    parent: str | None = None,
) -> dict:
    return {
        "contract": CONTRACT,
        "message_id": f"run-001-{kind}-{sequence}",
        "run_id": "run-001",
        "sequence": sequence,
        "kind": kind,
        "sender": {
            "name": name,
            "role_id": role_id,
            "driver_id": "codex",
            "model": "runtime-gpt",
        },
        "recipients": ["coordinator"],
        "in_reply_to": parent,
        "created_at": "2026-07-15T10:00:00Z",
        "payload": payload,
    }


def valid_chain() -> list[dict]:
    assignment = _envelope(
        1,
        "assignment",
        "hopper",
        "steward",
        {
            "summary": "Refactor one bounded harness module.",
            "assignee": {"name": "hamilton", "role_id": "senior-coder"},
            "target": "Implement provider-neutral message validation.",
            "base_revision": "335c1cd",
            "authority": {
                "read": ["src/fishtoucher/messages.py", "tests/test_messages.py"],
                "write": ["src/fishtoucher/messages.py"],
                "tools": ["repo.read", "repo.write", "shell.test"],
                "network": False,
                "delegate_roles": ["specialist-coder"],
            },
            "protected_paths": ["src/fishtoucher/invocations.py"],
            "context_sections": [
                {
                    "path": "src/fishtoucher/messages.py",
                    "start_line": 1,
                    "end_line": 120,
                    "purpose": "message contract",
                }
            ],
            "done_when": ["focused and full tests pass"],
            "required_commands": ["python3 -m unittest tests.test_messages -v"],
            "budget": {
                "max_context_sections": 2,
                "max_context_bytes": 12000,
                "max_delegated_calls": 1,
            },
            "escalate_when": ["scope expansion", "contract ambiguity"],
        },
    )
    result = _envelope(
        2,
        "result",
        "hamilton",
        "senior-coder",
        {
            "summary": "Candidate is ready for review.",
            "status": "completed",
            "changed_files": ["src/fishtoucher/messages.py"],
            "commands": ["python3 -m unittest tests.test_messages -v"],
            "patch_sha256": "a" * 64,
            "artifacts": [],
            "references": [],
            "delegated_invocations": [],
            "residual_risks": ["standalone runtime adapter is not enabled"],
        },
        assignment["message_id"],
    )
    verdict = _envelope(
        3,
        "verdict",
        "dijkstra",
        "cross-stack-verification-engineer",
        {
            "summary": "The bounded candidate is accepted.",
            "disposition": "accept",
            "defects": [],
            "evidence_checked": ["focused tests", "candidate diff"],
            "proof_boundary": ["message and mailbox structure"],
            "residual_risk": "Append-only storage is outside this proof.",
        },
        result["message_id"],
    )
    return [assignment, result, verdict]


def delegated_call(name: str = "ritchie") -> dict:
    return {
        "name": name,
        "role_id": "specialist-coder",
        "driver_id": "codex",
        "request_log": f"{name}-specialist-coder-req.json",
        "response_log": f"{name}-specialist-coder-resp.json",
        "request_sha256": "b" * 64,
        "response_sha256": "c" * 64,
        "status": "success",
    }


class MessageTests(unittest.TestCase):
    def test_three_record_chain_is_valid(self) -> None:
        chain = valid_chain()
        self.assertEqual(validate_mailbox(chain), [])
        self.assertTrue(all(not validate_message(item) for item in chain))

    def test_only_prototype_contract_and_four_kinds_are_allowed(self) -> None:
        broken = valid_chain()[0]
        broken["contract"] = "other-contract"
        self.assertTrue(any("contract" in item for item in validate_message(broken)))
        broken = valid_chain()[0]
        broken["kind"] = "ack"
        self.assertTrue(
            any("kind must be" in item for item in validate_message(broken))
        )

    def test_assignment_budgets_and_context_are_bounded(self) -> None:
        for field, value in (
            ("max_context_sections", 9),
            ("max_context_bytes", 32769),
            ("max_delegated_calls", 5),
        ):
            broken = valid_chain()[0]
            broken["payload"]["budget"][field] = value
            self.assertTrue(
                any("must not exceed" in item for item in validate_message(broken))
            )
        broken = valid_chain()[0]
        broken["payload"]["context_sections"] = []
        self.assertTrue(
            any("context_sections" in item for item in validate_message(broken))
        )

    def test_provider_neutral_delegated_logs_are_name_role_req_resp(self) -> None:
        result = valid_chain()[1]
        result["payload"]["delegated_invocations"] = [delegated_call()]
        self.assertEqual(validate_message(result), [])
        result["payload"]["delegated_invocations"][0]["request_log"] = "request.json"
        self.assertTrue(any("request_log" in item for item in validate_message(result)))

    def test_result_references_carry_external_issue_links(self) -> None:
        result = valid_chain()[1]
        result["payload"]["references"] = [
            "https://github.com/LinxISA/FishToucher/issues/1"
        ]
        self.assertEqual(validate_message(result), [])
        result["payload"]["references"] = [{"url": "not-compact"}]
        self.assertTrue(any("references" in item for item in validate_message(result)))

    def test_rejection_contains_executable_repair(self) -> None:
        verdict = valid_chain()[2]
        verdict["payload"]["disposition"] = "reject"
        self.assertTrue(
            any("concrete defect" in item for item in validate_message(verdict))
        )
        verdict["payload"]["defects"] = [
            {
                "id": "scope-leak",
                "severity": "high",
                "evidence": "candidate changes an unauthorized file",
                "required_fix": "revert the out-of-scope hunk",
                "write_scope": ["src/fishtoucher/messages.py"],
                "required_commands": ["python3 -m unittest tests.test_messages -v"],
            }
        ]
        self.assertEqual(validate_message(verdict), [])

    def test_result_cannot_escape_scope_or_delegation_authority(self) -> None:
        broken = valid_chain()
        broken[1]["payload"]["changed_files"] = ["README.md"]
        self.assertTrue(
            any("outside write scope" in item for item in validate_mailbox(broken))
        )
        broken = valid_chain()
        call = delegated_call()
        call["role_id"] = "isa-architect"
        call["request_log"] = "ritchie-isa-architect-req.json"
        call["response_log"] = "ritchie-isa-architect-resp.json"
        broken[1]["payload"]["delegated_invocations"] = [call]
        self.assertTrue(
            any(
                "outside assignment authority" in item
                for item in validate_mailbox(broken)
            )
        )

    def test_delegation_budget_and_self_review_are_enforced(self) -> None:
        broken = valid_chain()
        broken[1]["payload"]["delegated_invocations"] = [
            delegated_call("ritchie"),
            delegated_call("knuth"),
        ]
        self.assertTrue(
            any("exceed packet budget" in item for item in validate_mailbox(broken))
        )
        broken = valid_chain()
        broken[2]["sender"] = copy.deepcopy(broken[1]["sender"])
        self.assertTrue(any("self-verify" in item for item in validate_mailbox(broken)))

    def test_result_identity_and_reply_graph_are_enforced(self) -> None:
        broken = valid_chain()
        broken[1]["sender"]["name"] = "other"
        self.assertTrue(
            any("must match assignee" in item for item in validate_mailbox(broken))
        )
        broken = valid_chain()
        broken[2]["in_reply_to"] = broken[0]["message_id"]
        self.assertTrue(
            any("verdict must reply" in item for item in validate_mailbox(broken))
        )

    def test_invalid_changed_file_type_reports_without_crashing(self) -> None:
        broken = valid_chain()
        broken[1]["payload"]["changed_files"] = [{"bad": "path"}]
        self.assertTrue(validate_mailbox(broken))

    def test_loader_and_cli(self) -> None:
        chain = valid_chain()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            message_path = root / "message.json"
            mailbox_path = root / "mailbox.jsonl"
            message_path.write_text(json.dumps(chain[0]), encoding="utf-8")
            mailbox_path.write_text(
                "".join(json.dumps(item) + "\n" for item in chain), encoding="utf-8"
            )
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["message", str(message_path)]), 0)
                self.assertEqual(main(["mailbox", str(mailbox_path)]), 0)
            self.assertEqual(output.getvalue().count("PASS"), 2)
            mailbox_path.write_text("{}\nnot-json\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_mailbox(mailbox_path)


if __name__ == "__main__":
    unittest.main()
