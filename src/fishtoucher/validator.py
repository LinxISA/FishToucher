"""Validation rules for the FishToucher v1alpha1 flow contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

STANDARD = "fishtoucher.dev/v1alpha1"
LOOP_IDS = {"software", "architecture", "hardware"}
TERMINAL_STATUSES = {"pass", "fail", "timeout", "crash", "skipped", "waived"}


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


def _duplicate_ids(items: list[Any]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if isinstance(item_id, str):
            if item_id in seen:
                duplicates.add(item_id)
            seen.add(item_id)
    return duplicates


def validate_flow(flow: dict[str, Any]) -> list[str]:
    """Return all deterministic contract violations in a flow document."""

    errors: list[str] = []
    if flow.get("standard") != STANDARD:
        errors.append(f"standard must be {STANDARD!r}")

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
        actions = set(authority.get("exclusive_actions", []))
        missing = required_human_actions - actions
        if missing:
            errors.append(
                "human_authority.exclusive_actions is missing: "
                + ", ".join(sorted(missing))
            )

    pools = flow.get("model_pools", [])
    roles = flow.get("roles", [])
    gates = flow.get("gates", [])
    loops = flow.get("loops", [])
    for field, value in (
        ("model_pools", pools),
        ("roles", roles),
        ("gates", gates),
        ("loops", loops),
    ):
        if not isinstance(value, list) or not value:
            errors.append(f"{field} must be a non-empty array")

    if errors and not all(isinstance(value, list) for value in (pools, roles, gates, loops)):
        return errors

    for collection_name, collection in (
        ("model_pools", pools),
        ("roles", roles),
        ("gates", gates),
        ("loops", loops),
    ):
        duplicates = _duplicate_ids(collection)
        if duplicates:
            errors.append(
                f"{collection_name} contains duplicate ids: " + ", ".join(sorted(duplicates))
            )

    pool_by_id = {item.get("id"): item for item in pools if isinstance(item, dict)}
    role_by_id = {item.get("id"): item for item in roles if isinstance(item, dict)}
    gate_ids = {item.get("id") for item in gates if isinstance(item, dict)}

    providers = {pool.get("provider") for pool in pools if isinstance(pool, dict)}
    if "openai" not in providers or "deepseek" not in providers:
        errors.append("model_pools must include both openai and deepseek providers")

    for role in roles:
        if not isinstance(role, dict):
            errors.append("every role must be an object")
            continue
        role_id = role.get("id", "<unknown>")
        if role.get("model_pool") not in pool_by_id:
            errors.append(f"role {role_id!r} references an unknown model_pool")
        permissions = role.get("permissions")
        if not isinstance(permissions, dict):
            errors.append(f"role {role_id!r} must declare permissions")
            continue
        write_scopes = permissions.get("write", [])
        if not isinstance(write_scopes, list):
            errors.append(f"role {role_id!r} permissions.write must be an array")
        elif len(write_scopes) > 3:
            errors.append(f"role {role_id!r} may write at most three module scopes")
        for required in ("inputs", "outputs", "definition_of_done", "escalate_when"):
            if not role.get(required):
                errors.append(f"role {role_id!r} must declare {required}")

    actual_loop_ids = {item.get("id") for item in loops if isinstance(item, dict)}
    if actual_loop_ids != LOOP_IDS:
        errors.append(
            "loops must contain exactly: " + ", ".join(sorted(LOOP_IDS))
        )

    for loop in loops:
        if not isinstance(loop, dict):
            errors.append("every loop must be an object")
            continue
        loop_id = loop.get("id", "<unknown>")
        stages = loop.get("stages")
        if not isinstance(stages, list) or not stages:
            errors.append(f"loop {loop_id!r} must have non-empty stages")
            continue
        if not loop.get("inputs") or not loop.get("outputs"):
            errors.append(f"loop {loop_id!r} must declare inputs and outputs")
        if loop.get("stop_policy") != "first_red_hard_break":
            errors.append(f"loop {loop_id!r} must use first_red_hard_break stop_policy")
        for stage in stages:
            if not isinstance(stage, dict):
                errors.append(f"loop {loop_id!r} has a non-object stage")
                continue
            stage_id = stage.get("id", "<unknown>")
            actor_id = stage.get("actor")
            verifier_id = stage.get("verifier")
            if actor_id not in role_by_id:
                errors.append(f"stage {stage_id!r} references unknown actor {actor_id!r}")
            if verifier_id not in role_by_id:
                errors.append(f"stage {stage_id!r} references unknown verifier {verifier_id!r}")
            if actor_id == verifier_id:
                errors.append(f"stage {stage_id!r} actor cannot self-verify")
            if stage.get("gate") not in gate_ids:
                errors.append(f"stage {stage_id!r} references an unknown gate")
            if not stage.get("artifacts"):
                errors.append(f"stage {stage_id!r} must declare artifacts")
            actor = role_by_id.get(actor_id, {})
            verifier = role_by_id.get(verifier_id, {})
            actor_pool = pool_by_id.get(actor.get("model_pool"), {})
            verifier_pool = pool_by_id.get(verifier.get("model_pool"), {})
            if actor_pool and verifier_pool and actor_pool.get("provider") == verifier_pool.get("provider"):
                errors.append(
                    f"stage {stage_id!r} must use a different provider for independent verification"
                )

    anti_cheat = flow.get("anti_cheat", {})
    forbidden = set(anti_cheat.get("forbidden_changes", [])) if isinstance(anti_cheat, dict) else set()
    required_forbidden = {
        "delete_failing_test",
        "weaken_oracle",
        "swallow_exit_status",
        "shrink_required_suite",
        "print_only_pass",
    }
    missing_forbidden = required_forbidden - forbidden
    if missing_forbidden:
        errors.append("anti_cheat.forbidden_changes is missing: " + ", ".join(sorted(missing_forbidden)))

    return errors


def validate_evidence(evidence: dict[str, Any]) -> list[str]:
    """Validate a gate result without trusting agent-authored prose."""

    errors: list[str] = []
    required = (
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
        "agent",
    )
    for field in required:
        if field not in evidence:
            errors.append(f"missing evidence field: {field}")

    status = evidence.get("status")
    if status not in TERMINAL_STATUSES:
        errors.append("status must be one of: " + ", ".join(sorted(TERMINAL_STATUSES)))
    if status == "pass" and evidence.get("return_code") != 0:
        errors.append("pass evidence must have return_code 0")
    if status in {"timeout", "crash", "skipped"} and evidence.get("return_code") == 0:
        errors.append(f"{status} evidence cannot be represented as a successful return code")
    if status == "waived":
        waiver = evidence.get("waiver")
        if not isinstance(waiver, dict) or not all(
            waiver.get(field) for field in ("owner", "issue", "phase", "expires_utc")
        ):
            errors.append("waived evidence requires owner, issue, phase, and expires_utc")

    artifacts = evidence.get("artifacts", [])
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty array")
    else:
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("sha256"):
                errors.append(f"artifact {index} must include path and sha256")

    agent = evidence.get("agent", {})
    if not isinstance(agent, dict) or not all(agent.get(field) for field in ("role", "provider", "model", "prompt_revision")):
        errors.append("agent must include role, provider, model, and prompt_revision")
    return errors
