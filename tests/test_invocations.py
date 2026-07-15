"""Focused tests for the fishtoucher.invocation/v1 receipt validator and CLI command."""

from __future__ import annotations

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
from fishtoucher.invocations import PROTOCOL, validate_invocation_receipt  # noqa: E402


def _make_valid(**overrides):  # noqa: E302
    data = {
        "invocation": "inv-123",
        "run": "run-456",
        "packet": "pkt-789",
        "role": "deepseek_executor",
        "provider": "deepseek",
        "model": "deepseek-v4-pro",
        "transport": {
            "role": "adapter",
            "provider": "deepseek_adapter",
            "model": "adapter-v1",
        },
        "coordinator": {
            "role": "gpt_sensor",
            "provider": "openai",
            "model": "gpt-5.5",
        },
        "request_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "response_sha256": "a3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "started_at": "2026-07-15T10:00:00Z",
        "ended_at": "2026-07-15T10:01:00Z",
        "status": "success",
        "exit_code": 0,
        "protocol": PROTOCOL,
    }
    data.update(overrides)
    return data


class InvocationValidatorTests(unittest.TestCase):
    """Tests for the standalone validator function."""

    def test_valid_deepseek_receipt(self) -> None:
        receipt = _make_valid()
        errors = validate_invocation_receipt(receipt)
        self.assertEqual(errors, [])

    def test_missing_required_field(self) -> None:
        for field in {
            "invocation", "run", "packet", "role",
            "provider", "model", "transport", "coordinator",
            "request_sha256", "response_sha256",
            "started_at", "ended_at", "status", "exit_code", "protocol",
        }:
            receipt = _make_valid()
            del receipt[field]
            errors = validate_invocation_receipt(receipt)
            self.assertTrue(any("missing required field" in e for e in errors))

    def test_missing_protocol_fails(self) -> None:
        receipt = _make_valid()
        del receipt["protocol"]
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("missing required field" in e for e in errors))

    def test_wrong_protocol_fails(self) -> None:
        receipt = _make_valid(protocol="bad-protocol")
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("protocol" in e for e in errors))

    def test_unknown_field_rejected(self) -> None:
        receipt = _make_valid()
        receipt["secret_key"] = "abc"
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("unknown field" in e for e in errors))

    def test_blank_string_identities(self) -> None:
        for field in ("invocation", "run", "packet", "role", "provider", "model"):
            receipt = _make_valid()
            receipt[field] = "   "
            errors = validate_invocation_receipt(receipt)
            self.assertTrue(any(f"{field} must be a non-empty string" in e for e in errors))

    def test_malformed_sha256(self) -> None:
        for field in ("request_sha256", "response_sha256"):
            for bad in ("short", "z" * 64, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85"):
                receipt = _make_valid()
                receipt[field] = bad
                errors = validate_invocation_receipt(receipt)
                self.assertTrue(any("64-character hex" in e for e in errors))

    def test_invalid_timestamps(self) -> None:
        for field in ("started_at", "ended_at"):
            receipt = _make_valid()
            receipt[field] = "2026-07-15T10:00:00"  # missing Z
            errors = validate_invocation_receipt(receipt)
            self.assertTrue(any("valid UTC timestamp" in e for e in errors))
            receipt[field] = "2026-07-15T10:00:00Zzz"
            errors = validate_invocation_receipt(receipt)
            self.assertTrue(any("valid UTC timestamp" in e for e in errors))

    def test_ended_before_started(self) -> None:
        receipt = _make_valid()
        receipt["ended_at"] = "2026-07-15T09:59:00Z"
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("must not precede started_at" in e for e in errors))

    def test_status_exit_code_contradictions(self) -> None:
        # success with non-zero exit
        receipt = _make_valid(status="success", exit_code=1)
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("exit_code must be 0 when status is 'success'" in e for e in errors))
        # failure with zero exit
        receipt = _make_valid(status="failure", exit_code=0)
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("exit_code must not be 0 when status is 'failure'" in e for e in errors))

    def test_boolean_exit_code_rejected(self) -> None:
        receipt = _make_valid(exit_code=True)   # bool is not int under our check
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("integer (not boolean)" in e for e in errors))
        receipt = _make_valid(exit_code=False)
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("integer (not boolean)" in e for e in errors))

    def test_invalid_status_literal(self) -> None:
        receipt = _make_valid(status="ok")
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("must be 'success' or 'failure'" in e for e in errors))

    def test_identity_object_validation(self) -> None:
        # missing required field in transport
        receipt = _make_valid()
        del receipt["transport"]["role"]
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("transport missing required field" in e for e in errors))
        # unknown field in coordinator
        receipt = _make_valid()
        receipt["coordinator"]["capability"] = "x"
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("coordinator contains unknown field" in e for e in errors))
        # blank identity attribute
        receipt = _make_valid()
        receipt["transport"]["model"] = "  "
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("transport.model must be a non-empty string" in e for e in errors))

    def test_empty_dict_rejected(self) -> None:
        errors = validate_invocation_receipt({})
        self.assertTrue(errors)  # mentions missing required fields

    def test_prohibited_content_field_blocked(self) -> None:
        receipt = _make_valid()
        receipt["prompt"] = "secret"
        errors = validate_invocation_receipt(receipt)
        self.assertTrue(any("unknown field" in e and "prompt" in e for e in errors))


class InvocationCliTests(unittest.TestCase):
    """Tests for the CLI invocation command."""

    def _run_cli(self, content: str, *args) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "receipt.json"
            path.write_text(content, encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                rc = main(["invocation", str(path), *args])
            return rc, output.getvalue()

    def test_valid_receipt_passes(self) -> None:
        receipt = _make_valid()
        rc, out = self._run_cli(json.dumps(receipt))
        self.assertEqual(rc, 0)
        self.assertIn("PASS", out)

    def test_invalid_receipt_fails(self) -> None:
        receipt = _make_valid()
        del receipt["role"]
        rc, out = self._run_cli(json.dumps(receipt))
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)

    def test_cli_receipt_wrong_protocol_fails(self) -> None:
        receipt = _make_valid(protocol="wrong-protocol")
        rc, out = self._run_cli(json.dumps(receipt))
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)

    def test_broken_json_errors(self) -> None:
        rc, out = self._run_cli("{invalid")
        self.assertEqual(rc, 2)
        self.assertIn("ERROR", out)

    def test_non_existent_file_errors(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nope.json"
            output = StringIO()
            with redirect_stdout(output):
                rc = main(["invocation", str(path)])
            self.assertEqual(rc, 2)
            self.assertIn("ERROR", output.getvalue())


if __name__ == "__main__":
    unittest.main()
