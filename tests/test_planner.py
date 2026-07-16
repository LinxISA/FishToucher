from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishtoucher.planner import render_plan  # noqa: E402
from fishtoucher.validator import validate_flow  # noqa: E402


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = json.loads((ROOT / "config/linxisa.example.json").read_text())
        self.assertEqual(validate_flow(self.flow), [])

    def test_plan_uses_job_roles_not_providers(self) -> None:
        plan = render_plan(self.flow)
        self.assertIn("llvm-designer -> llvm-contract", plan)
        self.assertIn("qemu-verification-engineer", plan)
        self.assertIn("superproject-bringup-observer -> software-bringup", plan)
        self.assertNotIn("deepseek", plan.lower())

    def test_loop_selection_and_determinism(self) -> None:
        first = render_plan(self.flow, "hardware")
        self.assertEqual(first, render_plan(self.flow, "hardware"))
        self.assertIn("hardware-system-integration", first)
        self.assertNotIn("[software]", first)

    def test_unknown_loop(self) -> None:
        with self.assertRaises(ValueError):
            render_plan(self.flow, "unknown")


if __name__ == "__main__":
    unittest.main()
