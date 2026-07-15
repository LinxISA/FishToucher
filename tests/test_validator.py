from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishtoucher.planner import render_plan  # noqa: E402
from fishtoucher.validator import validate_evidence, validate_flow  # noqa: E402


def fixture(relative: str) -> dict:
    with (ROOT / relative).open(encoding="utf-8") as stream:
        return json.load(stream)


class FlowValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = fixture("config/linxisa.example.json")

    def test_example_flow_is_valid(self) -> None:
        self.assertEqual(validate_flow(self.flow), [])

    def test_implementer_cannot_self_verify(self) -> None:
        broken = copy.deepcopy(self.flow)
        stage = broken["loops"][0]["stages"][1]
        stage["verifier"] = stage["actor"]
        errors = validate_flow(broken)
        self.assertTrue(any("self-verify" in error for error in errors))

    def test_independent_verifier_uses_other_provider(self) -> None:
        broken = copy.deepcopy(self.flow)
        broken["loops"][0]["stages"][1]["verifier"] = "deepseek_verifier"
        errors = validate_flow(broken)
        self.assertTrue(any("different provider" in error for error in errors))

    def test_three_loops_are_exact(self) -> None:
        broken = copy.deepcopy(self.flow)
        broken["loops"].pop()
        errors = validate_flow(broken)
        self.assertTrue(any("exactly" in error for error in errors))

    def test_non_object_role_is_reported_without_crashing(self) -> None:
        broken = copy.deepcopy(self.flow)
        broken["roles"].append("not-a-role")
        errors = validate_flow(broken)
        self.assertIn("every role must be an object", errors)

    def test_hard_break_policy_is_required(self) -> None:
        broken = copy.deepcopy(self.flow)
        broken["loops"][0]["stop_policy"] = "continue_on_error"
        errors = validate_flow(broken)
        self.assertTrue(any("first_red_hard_break" in error for error in errors))

    def test_plan_is_stable_and_selectable(self) -> None:
        first = render_plan(self.flow, "software")
        second = render_plan(self.flow, "software")
        self.assertEqual(first, second)
        self.assertIn("software_implementation", first)
        self.assertNotIn("hardware_unit_implementation", first)


class EvidenceValidationTests(unittest.TestCase):
    def test_example_evidence_is_valid(self) -> None:
        self.assertEqual(validate_evidence(fixture("examples/evidence.pass.json")), [])

    def test_timeout_cannot_masquerade_as_success(self) -> None:
        broken = fixture("examples/evidence.pass.json")
        broken["status"] = "timeout"
        errors = validate_evidence(broken)
        self.assertTrue(any("successful return code" in error for error in errors))

    def test_waiver_needs_expiring_owner_record(self) -> None:
        broken = fixture("examples/evidence.pass.json")
        broken["status"] = "waived"
        errors = validate_evidence(broken)
        self.assertTrue(any("waived evidence requires" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
