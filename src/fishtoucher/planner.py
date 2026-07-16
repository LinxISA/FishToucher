"""Render deterministic role-driven plans from a validated flow."""

from __future__ import annotations

from typing import Any


def render_plan(flow: dict[str, Any], loop_id: str | None = None) -> str:
    loops = flow["loops"]
    if loop_id:
        loops = [loop for loop in loops if loop["id"] == loop_id]
        if not loops:
            raise ValueError(f"unknown loop: {loop_id}")
    lines: list[str] = []
    for loop in loops:
        lines.append(f"[{loop['id']}] {loop['purpose']}")
        lines.append(f"  stop-policy: {loop['stop_policy']}")
        for index, stage in enumerate(loop["stages"], start=1):
            verifiers = ",".join(stage["verifier_roles"])
            lines.append(
                f"  {index}. {stage['id']}: {stage['actor_role']} -> "
                f"{stage['gate']} -> {verifiers}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()
