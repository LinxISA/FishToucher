"""Validation for registry-driven FishToucher prototype flows and evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import (
    CONTRACT,
    is_integer,
    is_non_empty_string,
    is_sha256,
    is_slug,
    require_exact_fields,
    validate_string_list,
)

LOOP_IDS = {"software", "architecture", "hardware"}
TERMINAL_STATUSES = {"pass", "fail", "timeout", "crash", "skipped", "waived"}
BUDGET_LIMITS = {
    "max_context_sections": 8,
    "max_context_bytes": 32768,
    "max_delegated_calls": 4,
    "max_parallel_agents": 6,
    "max_depth": 2,
}
REQUIRED_ORG_CAPABILITIES = {
    "assignment.issue",
    "bringup.observe",
    "code.modify",
    "isa.compatibility.audit",
    "isa.golden.review",
    "work.review",
    "evidence.verify",
    "harness.optimize",
    "report.aggregate",
    "subagent.spawn",
}
ROLE_FIELDS = {
    "id",
    "title",
    "job_family",
    "objective",
    "capabilities",
    "permissions",
    "provider_policy",
    "inputs",
    "outputs",
    "definition_of_done",
    "escalate_when",
}
PERMISSION_FIELDS = {
    "read",
    "write",
    "tools",
    "network",
    "delegate_roles",
    "approve",
}
POLICY_FIELDS = {"preferred_drivers", "allowed_drivers"}
DRIVER_FIELDS = {
    "id",
    "kind",
    "provider",
    "model",
    "enabled",
    "capabilities",
    "credential_env",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("top-level JSON value must be an object")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _objects_by_id(
    value: Any, label: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a non-empty array")
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for item in value:
        if not isinstance(item, dict):
            errors.append(f"every {label} item must be an object")
            continue
        item_id = item.get("id")
        if not is_slug(item_id):
            errors.append(f"every {label} id must be a short kebab-case string")
            continue
        if item_id in indexed:
            errors.append(f"{label} contains duplicate id: {item_id}")
        indexed[item_id] = item
    return indexed


def _validate_driver(driver: dict[str, Any], errors: list[str]) -> None:
    driver_id = driver.get("id", "<unknown>")
    errors.extend(require_exact_fields(driver, DRIVER_FIELDS, f"driver {driver_id!r}"))
    for field in ("kind", "provider", "model"):
        if not is_non_empty_string(driver.get(field)):
            errors.append(f"driver {driver_id!r}.{field} must be a non-empty string")
    if not isinstance(driver.get("enabled"), bool):
        errors.append(f"driver {driver_id!r}.enabled must be boolean")
    errors.extend(
        validate_string_list(
            driver.get("capabilities"),
            f"driver {driver_id!r}.capabilities",
            non_empty=True,
        )
    )
    credential_env = driver.get("credential_env")
    if credential_env is not None and not is_non_empty_string(credential_env):
        errors.append(
            f"driver {driver_id!r}.credential_env must be null or a variable name"
        )


def _validate_role(
    role: dict[str, Any],
    roles: dict[str, dict[str, Any]],
    drivers: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    role_id = role.get("id", "<unknown>")
    errors.extend(require_exact_fields(role, ROLE_FIELDS, f"role {role_id!r}"))
    for field in ("title", "job_family", "objective"):
        if not is_non_empty_string(role.get(field)):
            errors.append(f"role {role_id!r}.{field} must be a non-empty string")
    for field in (
        "capabilities",
        "inputs",
        "outputs",
        "definition_of_done",
        "escalate_when",
    ):
        errors.extend(
            validate_string_list(
                role.get(field), f"role {role_id!r}.{field}", non_empty=True
            )
        )

    permissions = role.get("permissions")
    errors.extend(
        require_exact_fields(
            permissions, PERMISSION_FIELDS, f"role {role_id!r}.permissions"
        )
    )
    permission_map = permissions if isinstance(permissions, dict) else {}
    if permission_map:
        for field in ("read", "write", "tools", "delegate_roles", "approve"):
            errors.extend(
                validate_string_list(
                    permission_map.get(field),
                    f"role {role_id!r}.permissions.{field}",
                    non_empty=field in {"read", "tools"},
                )
            )
        if not isinstance(permission_map.get("network"), bool):
            errors.append(f"role {role_id!r}.permissions.network must be boolean")
        for delegated in permission_map.get("delegate_roles", []):
            if isinstance(delegated, str) and delegated not in roles:
                errors.append(
                    f"role {role_id!r} delegates to unknown role {delegated!r}"
                )

    raw_capabilities = role.get("capabilities", [])
    capabilities = (
        {item for item in raw_capabilities if isinstance(item, str)}
        if isinstance(raw_capabilities, list)
        else set()
    )
    writes = permission_map.get("write", [])
    if "code.modify" in capabilities and not writes:
        errors.append(f"role {role_id!r} with code.modify needs bounded write scopes")
    if "work.review" in capabilities and "code.modify" in capabilities:
        errors.append(f"role {role_id!r} cannot both implement and review")
    if "work.review" in capabilities and writes:
        errors.append(f"review role {role_id!r} must be read-only")

    policy = role.get("provider_policy")
    errors.extend(
        require_exact_fields(policy, POLICY_FIELDS, f"role {role_id!r}.provider_policy")
    )
    if not isinstance(policy, dict):
        return
    preferred = policy.get("preferred_drivers")
    allowed = policy.get("allowed_drivers")
    errors.extend(
        validate_string_list(
            preferred,
            f"role {role_id!r}.provider_policy.preferred_drivers",
            non_empty=True,
        )
    )
    errors.extend(
        validate_string_list(
            allowed,
            f"role {role_id!r}.provider_policy.allowed_drivers",
            non_empty=True,
        )
    )
    valid_driver_lists = (
        isinstance(preferred, list)
        and isinstance(allowed, list)
        and all(isinstance(item, str) for item in preferred + allowed)
    )
    if valid_driver_lists:
        if not set(preferred) <= set(allowed):
            errors.append(f"role {role_id!r} preferred drivers must be allowed")
        for driver_id in allowed:
            if driver_id not in drivers:
                errors.append(
                    f"role {role_id!r} references unknown driver {driver_id!r}"
                )
        if not any(drivers.get(item, {}).get("enabled") for item in preferred):
            errors.append(f"role {role_id!r} needs an enabled preferred driver")
        raw_tools = permission_map.get("tools", [])
        required_tools = (
            {item for item in raw_tools if isinstance(item, str)}
            if isinstance(raw_tools, list)
            else set()
        )
        enabled_tools: set[str] = set()
        for driver_id in allowed:
            driver = drivers.get(driver_id, {})
            if driver.get("enabled"):
                capabilities = driver.get("capabilities", [])
                if isinstance(capabilities, list):
                    enabled_tools.update(
                        item for item in capabilities if isinstance(item, str)
                    )
        missing_tools = required_tools - enabled_tools
        if missing_tools:
            errors.append(
                f"role {role_id!r} has no enabled driver for tools: "
                + ", ".join(sorted(missing_tools))
            )


def validate_flow(flow: dict[str, Any]) -> list[str]:
    """Return deterministic violations without hard-coding role identifiers."""

    errors: list[str] = []
    if flow.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT!r}")
    if not isinstance(flow.get("project"), dict):
        errors.append("project must be an object")

    authority = flow.get("human_authority")
    required_human_actions = {
        "freeze_interface",
        "approve_waiver",
        "resolve_model_conflict",
        "promote_release",
    }
    if not isinstance(authority, dict):
        errors.append("human_authority must be an object")
    else:
        raw_actions = authority.get("exclusive_actions", [])
        actions = (
            {action for action in raw_actions if isinstance(action, str)}
            if isinstance(raw_actions, list)
            else set()
        )
        missing = required_human_actions - actions
        if missing:
            errors.append(
                "human_authority.exclusive_actions is missing: "
                + ", ".join(sorted(missing))
            )

    drivers = _objects_by_id(flow.get("drivers"), "drivers", errors)
    roles = _objects_by_id(flow.get("roles"), "roles", errors)
    gates = _objects_by_id(flow.get("gates"), "gates", errors)
    loops = _objects_by_id(flow.get("loops"), "loops", errors)
    for driver in drivers.values():
        _validate_driver(driver, errors)
    for role in roles.values():
        _validate_role(role, roles, drivers, errors)

    declared_capabilities = {
        capability
        for role in roles.values()
        for capability in role.get("capabilities", [])
        if isinstance(capability, str)
    }
    missing_capabilities = REQUIRED_ORG_CAPABILITIES - declared_capabilities
    if missing_capabilities:
        errors.append(
            "organization is missing capabilities: "
            + ", ".join(sorted(missing_capabilities))
        )

    budgets = flow.get("budgets")
    if not isinstance(budgets, dict):
        errors.append("budgets must be an object")
    else:
        for field, maximum in BUDGET_LIMITS.items():
            value = budgets.get(field)
            minimum = 0 if field == "max_delegated_calls" else 1
            if not is_integer(value) or value < minimum:
                errors.append(f"budgets.{field} must be an integer >= {minimum}")
            elif value > maximum:
                errors.append(f"budgets.{field} must not exceed {maximum}")

    if set(loops) != LOOP_IDS:
        errors.append("loops must contain exactly: " + ", ".join(sorted(LOOP_IDS)))
    used_gates: set[str] = set()
    for loop_id, loop in loops.items():
        if loop.get("stop_policy") != "first_red_hard_break":
            errors.append(f"loop {loop_id!r} must use first_red_hard_break")
        for field in ("purpose", "inputs", "outputs"):
            if not loop.get(field):
                errors.append(f"loop {loop_id!r} must declare {field}")
        stages = loop.get("stages")
        if not isinstance(stages, list) or not stages:
            errors.append(f"loop {loop_id!r} must have non-empty stages")
            continue
        for stage in stages:
            if not isinstance(stage, dict):
                errors.append(f"loop {loop_id!r} has a non-object stage")
                continue
            stage_id = stage.get("id", "<unknown>")
            actor_id = stage.get("actor_role")
            verifier_ids = stage.get("verifier_roles")
            gate_id = stage.get("gate")
            actor = roles.get(actor_id, {}) if isinstance(actor_id, str) else {}
            if not isinstance(actor_id, str) or actor_id not in roles:
                errors.append(
                    f"stage {stage_id!r} references unknown actor {actor_id!r}"
                )
            if not isinstance(verifier_ids, list) or not verifier_ids:
                errors.append(f"stage {stage_id!r} needs verifier_roles")
                verifier_ids = []
            for verifier_id in verifier_ids:
                if not isinstance(verifier_id, str):
                    errors.append(f"stage {stage_id!r} verifier ids must be strings")
                    continue
                verifier = roles.get(verifier_id)
                if verifier is None:
                    errors.append(
                        f"stage {stage_id!r} references unknown verifier {verifier_id!r}"
                    )
                    continue
                verifier_values = verifier.get("capabilities", [])
                verifier_capabilities = (
                    {item for item in verifier_values if isinstance(item, str)}
                    if isinstance(verifier_values, list)
                    else set()
                )
                if not verifier_capabilities & {"work.review", "evidence.verify"}:
                    errors.append(
                        f"stage {stage_id!r} verifier {verifier_id!r} lacks review capability"
                    )
                if verifier_id == actor_id:
                    errors.append(f"stage {stage_id!r} actor cannot self-verify")
            if not isinstance(gate_id, str) or gate_id not in gates:
                errors.append(f"stage {stage_id!r} references unknown gate")
            else:
                used_gates.add(gate_id)
            raw_required = stage.get("required_capabilities", [])
            if not isinstance(raw_required, list) or not all(
                isinstance(item, str) for item in raw_required
            ):
                errors.append(
                    f"stage {stage_id!r} required_capabilities must be strings"
                )
                raw_required = []
            required = set(raw_required)
            actor_values = actor.get("capabilities", [])
            actor_capabilities = (
                {item for item in actor_values if isinstance(item, str)}
                if isinstance(actor_values, list)
                else set()
            )
            missing = required - actor_capabilities
            if missing:
                errors.append(
                    f"stage {stage_id!r} actor lacks capabilities: "
                    + ", ".join(sorted(missing))
                )
            if not stage.get("artifacts"):
                errors.append(f"stage {stage_id!r} must declare artifacts")
    unused = set(gates) - used_gates
    if unused:
        errors.append("unused gates: " + ", ".join(sorted(unused)))

    anti_cheat = flow.get("anti_cheat")
    required_forbidden = {
        "delete_failing_test",
        "weaken_oracle",
        "swallow_exit_status",
        "shrink_required_suite",
        "print_only_pass",
    }
    raw_forbidden = (
        anti_cheat.get("forbidden_changes", []) if isinstance(anti_cheat, dict) else []
    )
    forbidden = (
        {item for item in raw_forbidden if isinstance(item, str)}
        if isinstance(raw_forbidden, list)
        else set()
    )
    missing_forbidden = required_forbidden - forbidden
    if missing_forbidden:
        errors.append(
            "anti_cheat.forbidden_changes is missing: "
            + ", ".join(sorted(missing_forbidden))
        )
    return errors


def validate_evidence(evidence: dict[str, Any]) -> list[str]:
    """Validate gate evidence without trusting agent-authored prose."""

    errors: list[str] = []
    required = {
        "contract",
        "kind",
        "run_id",
        "profile",
        "lane",
        "gate_id",
        "command",
        "cwd",
        "started_at",
        "finished_at",
        "status",
        "return_code",
        "artifacts",
        "sha_manifest",
        "dirty_tree",
        "actor",
    }
    for field in sorted(required - set(evidence)):
        errors.append(f"missing evidence field: {field}")
    if evidence.get("contract") != CONTRACT:
        errors.append(f"contract must be {CONTRACT!r}")
    if evidence.get("kind") != "evidence":
        errors.append("kind must be 'evidence'")
    status = evidence.get("status")
    if status not in TERMINAL_STATUSES:
        errors.append("invalid evidence status")
    if status == "pass" and evidence.get("return_code") != 0:
        errors.append("pass evidence must have return_code 0")
    if status in {"timeout", "crash", "skipped"} and evidence.get("return_code") == 0:
        errors.append(f"{status} evidence cannot have a successful return code")
    if status == "waived":
        waiver = evidence.get("waiver")
        if not isinstance(waiver, dict) or not all(
            waiver.get(field) for field in ("owner", "issue", "phase", "expires_utc")
        ):
            errors.append(
                "waived evidence requires owner, issue, phase, and expires_utc"
            )
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty array")
    else:
        for index, artifact in enumerate(artifacts):
            if (
                not isinstance(artifact, dict)
                or not is_non_empty_string(artifact.get("path"))
                or not is_sha256(artifact.get("sha256"))
            ):
                errors.append(f"artifact {index} must include path and sha256")
    actor = evidence.get("actor")
    if not isinstance(actor, dict) or not all(
        actor.get(field) for field in ("name", "role_id", "driver_id", "model")
    ):
        errors.append("actor must include name, role_id, driver_id, and model")
    return errors
