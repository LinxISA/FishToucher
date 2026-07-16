from __future__ import annotations

import json
import os
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
from fishtoucher.invocations import (  # noqa: E402
    invocation_log_names,
    validate_invocation_receipt,
    write_invocation_logs,
)


def valid_receipt(**overrides) -> dict:
    data = {
        "contract": CONTRACT,
        "kind": "invocation",
        "invocation_id": "inv-123",
        "run_id": "run-456",
        "assignment_id": "assignment-789",
        "actor": {"name": "ritchie", "role_id": "specialist-coder"},
        "driver": {
            "id": "codex",
            "kind": "codex-native-or-sdk",
            "provider": "openai",
            "model": "runtime-gpt",
        },
        "request_log": "ritchie-specialist-coder-req.json",
        "response_log": "ritchie-specialist-coder-resp.json",
        "request_sha256": "a" * 64,
        "response_sha256": "b" * 64,
        "started_at": "2026-07-15T10:00:00Z",
        "ended_at": "2026-07-15T10:01:00Z",
        "status": "success",
        "exit_code": 0,
        "usage": {"input_tokens": 100, "output_tokens": 20},
        "tool_actions": ["repo.read"],
    }
    data.update(overrides)
    return data


class InvocationTests(unittest.TestCase):
    def test_provider_neutral_receipt_is_valid(self) -> None:
        self.assertEqual(validate_invocation_receipt(valid_receipt()), [])
        receipt = valid_receipt()
        receipt["driver"].update(
            id="deepseek", provider="deepseek", model="runtime-deepseek"
        )
        self.assertEqual(validate_invocation_receipt(receipt), [])

    def test_unknown_or_raw_content_fields_are_rejected(self) -> None:
        receipt = valid_receipt()
        receipt["prompt"] = "must not be embedded"
        self.assertTrue(
            any("unexpected" in item for item in validate_invocation_receipt(receipt))
        )

    def test_log_names_are_bound_to_name_and_role(self) -> None:
        self.assertEqual(
            invocation_log_names("hamilton", "senior-coder"),
            ("hamilton-senior-coder-req.json", "hamilton-senior-coder-resp.json"),
        )
        broken = valid_receipt(request_log="request.json")
        self.assertTrue(
            any("request_log" in item for item in validate_invocation_receipt(broken))
        )

    def test_status_time_hash_and_usage_are_checked(self) -> None:
        for receipt in (
            valid_receipt(status="failure", exit_code=0),
            valid_receipt(ended_at="2026-07-15T09:00:00Z"),
            valid_receipt(request_sha256="bad"),
            valid_receipt(usage={"input_tokens": -1, "output_tokens": 0}),
        ):
            self.assertTrue(validate_invocation_receipt(receipt))

    def test_logs_are_create_once_mode_0600_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = write_invocation_logs(
                directory,
                "ritchie",
                "specialist-coder",
                {"target": "bounded task"},
                {"status": "completed"},
            )
            request = Path(directory) / result["request_log"]
            self.assertEqual(os.stat(request).st_mode & 0o777, 0o600)
            self.assertEqual(len(result["request_sha256"]), 64)
            with self.assertRaises(FileExistsError):
                write_invocation_logs(
                    directory,
                    "ritchie",
                    "specialist-coder",
                    {},
                    {},
                )

    def test_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(valid_receipt()), encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["invocation", str(path)]), 0)
            self.assertIn("PASS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
