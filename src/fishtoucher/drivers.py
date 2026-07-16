"""Provider-neutral driver selection and effective-permission helpers."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Any, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class DriverRequest:
    """One already-authorized role assignment passed to an execution driver."""

    run_id: str
    assignment_id: str
    actor_name: str
    role_id: str
    cwd: str
    assignment: Mapping[str, Any]


@dataclass(frozen=True)
class DriverResult:
    """In-memory driver result before compact logs and receipts are persisted."""

    handle: str
    status: str
    response: Any
    input_tokens: int
    output_tokens: int
    tool_actions: tuple[str, ...]


@runtime_checkable
class AgentDriver(Protocol):
    """Common lifecycle implemented by Codex, DeepSeek, and test drivers."""

    id: str
    capabilities: frozenset[str]

    def start(self, request: DriverRequest) -> str: ...

    def follow_up(self, handle: str, message: Mapping[str, Any]) -> None: ...

    def wait(self, handle: str) -> DriverResult: ...

    def cancel(self, handle: str) -> None: ...


class DriverSelectionError(ValueError):
    """Raised when no configured driver can execute a role assignment."""


def _safe_repo_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts


def path_allowed(path: str, scopes: list[str]) -> bool:
    """Return whether a safe repository-relative path matches an allowed scope."""

    return _safe_repo_path(path) and any(fnmatchcase(path, scope) for scope in scopes)


def select_driver(
    flow: dict[str, Any],
    role_id: str,
    required_tools: set[str] | None = None,
) -> dict[str, Any]:
    """Select the first enabled preferred driver satisfying required tools."""

    roles = {
        role["id"]: role
        for role in flow.get("roles", [])
        if isinstance(role, dict) and isinstance(role.get("id"), str)
    }
    drivers = {
        driver["id"]: driver
        for driver in flow.get("drivers", [])
        if isinstance(driver, dict) and isinstance(driver.get("id"), str)
    }
    role = roles.get(role_id)
    if role is None:
        raise DriverSelectionError(f"unknown role: {role_id}")

    policy = role.get("provider_policy", {})
    needed = set(required_tools or role.get("permissions", {}).get("tools", []))
    for driver_id in policy.get("preferred_drivers", []):
        driver = drivers.get(driver_id)
        if not driver or not driver.get("enabled"):
            continue
        if needed <= set(driver.get("capabilities", [])):
            return driver
    raise DriverSelectionError(
        f"no enabled preferred driver for role {role_id!r} supports: "
        + ", ".join(sorted(needed))
    )


def effective_permissions(
    role: dict[str, Any],
    assignment: dict[str, Any],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    """Intersect role, assignment, and runtime authority without widening scope."""

    role_permissions = role["permissions"]
    authority = assignment["authority"]
    read_scope = [
        path
        for path in authority["read"]
        if path_allowed(path, role_permissions["read"])
        and path_allowed(path, runtime["read"])
    ]
    write_scope = [
        path
        for path in authority["write"]
        if path_allowed(path, role_permissions["write"])
        and path_allowed(path, runtime["write"])
    ]
    return {
        "read": read_scope,
        "write": write_scope,
        "tools": sorted(
            set(role_permissions["tools"])
            & set(authority["tools"])
            & set(runtime["tools"])
        ),
        "network": bool(
            role_permissions["network"] and authority["network"] and runtime["network"]
        ),
        "delegate_roles": sorted(
            set(role_permissions["delegate_roles"])
            & set(authority["delegate_roles"])
            & set(runtime["delegate_roles"])
        ),
    }
