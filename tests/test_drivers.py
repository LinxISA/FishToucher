from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fishtoucher.drivers import (  # noqa: E402
    AgentDriver,
    DriverRequest,
    DriverResult,
    DriverSelectionError,
    effective_permissions,
    path_allowed,
    select_driver,
)


class StubDriver:
    id = "stub"
    capabilities = frozenset({"repo.read"})

    def start(self, request: DriverRequest) -> str:
        return request.assignment_id

    def follow_up(self, handle: str, message: dict) -> None:
        return None

    def wait(self, handle: str) -> DriverResult:
        return DriverResult(handle, "success", {}, 0, 0, ())

    def cancel(self, handle: str) -> None:
        return None


class DriverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.flow = json.loads((ROOT / "config/linxisa.example.json").read_text())

    def test_path_scope_rejects_traversal_and_absolute_paths(self) -> None:
        self.assertTrue(path_allowed("src/fishtoucher/cli.py", ["src/**"]))
        self.assertFalse(path_allowed("../secret", ["**"]))
        self.assertFalse(path_allowed("/tmp/secret", ["**"]))

    def test_common_driver_lifecycle_matches_native_and_external_lanes(self) -> None:
        driver = StubDriver()
        self.assertIsInstance(driver, AgentDriver)
        request = DriverRequest(
            "run-1", "assignment-1", "ritchie", "specialist-coder", ".", {}
        )
        handle = driver.start(request)
        driver.follow_up(handle, {"repair": "bounded"})
        self.assertEqual(driver.wait(handle).status, "success")
        driver.cancel(handle)

    def test_permission_intersection_never_widens_assignment(self) -> None:
        role = {
            "permissions": {
                "read": ["src/**"],
                "write": ["src/**"],
                "tools": ["repo.read", "repo.write", "shell.test"],
                "network": True,
                "delegate_roles": ["specialist-coder"],
            }
        }
        assignment = {
            "authority": {
                "read": ["src/fishtoucher/cli.py", "README.md"],
                "write": ["src/fishtoucher/cli.py", "README.md"],
                "tools": ["repo.read", "repo.write"],
                "network": True,
                "delegate_roles": ["specialist-coder"],
            }
        }
        runtime = {
            "read": ["src/**"],
            "write": ["src/fishtoucher/**"],
            "tools": ["repo.read"],
            "network": False,
            "delegate_roles": [],
        }
        effective = effective_permissions(role, assignment, runtime)
        self.assertEqual(effective["write"], ["src/fishtoucher/cli.py"])
        self.assertEqual(effective["tools"], ["repo.read"])
        self.assertFalse(effective["network"])
        self.assertEqual(effective["delegate_roles"], [])

    def test_driver_selection_is_deterministic_and_capability_checked(self) -> None:
        self.assertEqual(select_driver(self.flow, "senior-coder")["id"], "codex")
        with self.assertRaises(DriverSelectionError):
            select_driver(self.flow, "senior-coder", {"hardware.flash"})
        with self.assertRaises(DriverSelectionError):
            select_driver(self.flow, "unknown")


if __name__ == "__main__":
    unittest.main()
