from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishtoucher.drivers import select_driver  # noqa: E402
from fishtoucher.validator import validate_evidence, validate_flow  # noqa: E402


def fixture(path: str) -> dict:
    with (ROOT / path).open(encoding="utf-8") as stream:
        return json.load(stream)


class FlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = fixture("config/linxisa.example.json")

    def test_example_is_valid_and_defaults_to_all_gpt(self) -> None:
        self.assertEqual(validate_flow(self.flow), [])
        self.assertFalse(
            next(item for item in self.flow["drivers"] if item["id"] == "deepseek")[
                "enabled"
            ]
        )
        self.assertEqual(select_driver(self.flow, "specialist-coder")["id"], "codex")

    def test_optional_deepseek_driver_can_be_selected_without_role_changes(
        self,
    ) -> None:
        flow = copy.deepcopy(self.flow)
        next(item for item in flow["drivers"] if item["id"] == "deepseek")[
            "enabled"
        ] = True
        role = next(item for item in flow["roles"] if item["id"] == "specialist-coder")
        role["provider_policy"]["preferred_drivers"] = ["deepseek", "codex"]
        self.assertEqual(validate_flow(flow), [])
        self.assertEqual(select_driver(flow, "specialist-coder")["id"], "deepseek")

    def test_new_role_loads_without_runtime_code_change(self) -> None:
        flow = copy.deepcopy(self.flow)
        role = copy.deepcopy(
            next(item for item in flow["roles"] if item["id"] == "harness-auditor")
        )
        role["id"] = "memory-system-reviewer"
        role["title"] = "Memory System Reviewer"
        flow["roles"].append(role)
        self.assertEqual(validate_flow(flow), [])

    def test_role_and_stage_capabilities_enforce_separation(self) -> None:
        flow = copy.deepcopy(self.flow)
        stage = flow["loops"][0]["stages"][1]
        stage["verifier_roles"] = [stage["actor_role"]]
        self.assertTrue(any("self-verify" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        reviewer = next(
            item for item in flow["roles"] if item["id"] == "harness-auditor"
        )
        reviewer["permissions"]["write"] = ["src/**"]
        self.assertTrue(any("read-only" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        flow["loops"][0]["stages"][1]["actor_role"] = "harness-auditor"
        self.assertTrue(
            any("actor lacks capabilities" in item for item in validate_flow(flow))
        )

    def test_driver_references_and_tool_support_are_validated(self) -> None:
        flow = copy.deepcopy(self.flow)
        role = next(item for item in flow["roles"] if item["id"] == "senior-coder")
        role["provider_policy"]["preferred_drivers"] = ["missing"]
        role["provider_policy"]["allowed_drivers"] = ["missing"]
        self.assertTrue(any("unknown driver" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        role = next(item for item in flow["roles"] if item["id"] == "senior-coder")
        role["permissions"]["tools"].append("hardware.flash")
        self.assertTrue(
            any("no enabled driver" in item for item in validate_flow(flow))
        )

    def test_malformed_role_fields_report_without_crashing(self) -> None:
        flow = copy.deepcopy(self.flow)
        role = next(item for item in flow["roles"] if item["id"] == "senior-coder")
        role["permissions"] = "invalid"
        role["provider_policy"]["allowed_drivers"] = [{"bad": "id"}]
        self.assertTrue(validate_flow(flow))

    def test_organization_requires_delivery_review_evidence_and_optimization(
        self,
    ) -> None:
        flow = copy.deepcopy(self.flow)
        role = next(
            item
            for item in flow["roles"]
            if item["id"] == "harness-efficiency-engineer"
        )
        role["capabilities"].remove("harness.optimize")
        self.assertTrue(
            any("organization is missing" in item for item in validate_flow(flow))
        )

    def test_steward_is_the_human_interface_and_can_spawn_every_job(self) -> None:
        roles = {item["id"]: item for item in self.flow["roles"]}
        steward = roles["steward"]
        self.assertEqual(self.flow["project"]["display_name"], "乱序摸鱼")
        self.assertEqual(self.flow["human_authority"]["interface_role"], "steward")
        self.assertTrue(
            {"assignment.issue", "subagent.spawn", "report.aggregate"}
            <= set(steward["capabilities"])
        )
        self.assertEqual(
            set(steward["permissions"]["delegate_roles"]), set(roles) - {"steward"}
        )

    def test_linxisa_jobs_have_tight_domain_authority(self) -> None:
        roles = {item["id"]: item for item in self.flow["roles"]}
        required = {
            "steward",
            "isa-architect",
            "isa-verification-engineer",
            "qemu-designer",
            "qemu-verification-engineer",
            "llvm-designer",
            "llvm-verification-engineer",
            "superproject-bringup-observer",
        }
        self.assertTrue(required <= set(roles))
        self.assertEqual(roles["isa-architect"]["permissions"]["write"], [])
        traffic = roles["isa-verification-engineer"]
        self.assertEqual(traffic["permissions"]["write"], [])
        self.assertTrue(traffic["permissions"]["network"])
        self.assertIn("issue.write", traffic["permissions"]["tools"])
        self.assertEqual(
            roles["qemu-designer"]["permissions"]["write"], ["emulator/qemu/**"]
        )
        self.assertEqual(
            roles["llvm-designer"]["permissions"]["write"], ["compiler/llvm/**"]
        )
        self.assertEqual(
            set(roles["qemu-verification-engineer"]["permissions"]["write"]),
            {"avs/qemu/**", "emulator/qemu/tests/**"},
        )
        self.assertEqual(
            set(roles["llvm-verification-engineer"]["permissions"]["write"]),
            {
                "avs/compiler/linx-llvm/tests/**",
                "compiler/llvm/llvm/test/**",
                "compiler/llvm/clang/test/**",
            },
        )
        observer = roles["superproject-bringup-observer"]
        self.assertEqual(observer["permissions"]["write"], [])
        self.assertIn("bringup.observe", observer["capabilities"])
        for role_id in required:
            role = roles[role_id]
            self.assertTrue(role["objective"])
            self.assertTrue(role["outputs"])
            self.assertTrue(role["definition_of_done"])
            self.assertTrue(role["escalate_when"])

    def test_every_role_has_a_takeover_prompt(self) -> None:
        missing = [
            item["id"]
            for item in self.flow["roles"]
            if not (ROOT / "prompts" / f"{item['id']}.md").is_file()
        ]
        self.assertEqual(missing, [])

    def test_steward_prompt_requires_takeover_before_spawn(self) -> None:
        prompt = (ROOT / "prompts/steward.md").read_text(encoding="utf-8")
        self.assertIn("已接管“乱序摸鱼”管家角色。", prompt)
        self.assertIn("before spawning", prompt)
        self.assertLess(prompt.index("## Takeover"), prompt.index("## Operate"))

    def test_budgets_loops_gates_and_contract_are_checked(self) -> None:
        flow = copy.deepcopy(self.flow)
        flow["contract"] = "other"
        self.assertTrue(any("contract" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        flow["budgets"]["max_depth"] = 3
        self.assertTrue(any("must not exceed" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        flow["loops"].pop()
        self.assertTrue(any("exactly" in item for item in validate_flow(flow)))
        flow = copy.deepcopy(self.flow)
        flow["loops"][1]["stages"] = flow["loops"][1]["stages"][:1]
        self.assertTrue(any("unused gates" in item for item in validate_flow(flow)))


class EvidenceTests(unittest.TestCase):
    def test_example_is_valid(self) -> None:
        self.assertEqual(validate_evidence(fixture("examples/evidence.pass.json")), [])

    def test_contract_and_nonpass_status_are_honest(self) -> None:
        evidence = fixture("examples/evidence.pass.json")
        evidence["contract"] = "other"
        self.assertTrue(any("contract" in item for item in validate_evidence(evidence)))
        evidence = fixture("examples/evidence.pass.json")
        evidence["status"] = "timeout"
        self.assertTrue(
            any("successful" in item for item in validate_evidence(evidence))
        )

    def test_waiver_needs_human_record(self) -> None:
        evidence = fixture("examples/evidence.pass.json")
        evidence["status"] = "waived"
        self.assertTrue(
            any("waived evidence" in item for item in validate_evidence(evidence))
        )


if __name__ == "__main__":
    unittest.main()
