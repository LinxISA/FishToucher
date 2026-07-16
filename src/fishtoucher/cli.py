"""Command-line validation and routing for the FishToucher prototype."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .contracts import CONTRACT
from .drivers import DriverSelectionError, select_driver
from .invocations import validate_invocation_receipt
from .messages import load_mailbox, validate_mailbox, validate_message
from .planner import render_plan
from .validator import load_json, validate_evidence, validate_flow


def _report(errors: list[str], path: Path) -> int:
    if not errors:
        print(f"PASS {path}")
        return 0
    print(f"FAIL {path}")
    for error in errors:
        print(f"- {error}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fishtoucher")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("validate", "validate a flow"),
        ("evidence", "validate gate evidence"),
        ("message", "validate one message"),
        ("mailbox", "validate an ordered mailbox"),
        ("invocation", "validate an invocation receipt"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("path", type=Path)
    plan = commands.add_parser("plan", help="render the deterministic role plan")
    plan.add_argument("path", type=Path)
    plan.add_argument("--loop", choices=("software", "architecture", "hardware"))
    role = commands.add_parser("role", help="print one registered Role Card")
    role.add_argument("path", type=Path)
    role.add_argument("role_id")
    route = commands.add_parser("route", help="select a driver for a role")
    route.add_argument("path", type=Path)
    route.add_argument("role_id")
    route.add_argument("--tool", action="append", default=[])
    commands.add_parser("contract", help="print the prototype contract marker")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "contract":
        print(CONTRACT)
        return 0
    try:
        if args.command == "mailbox":
            document: Any = load_mailbox(args.path)
        else:
            document = load_json(args.path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 2

    if args.command == "validate":
        return _report(validate_flow(document), args.path)
    if args.command == "evidence":
        return _report(validate_evidence(document), args.path)
    if args.command == "message":
        return _report(validate_message(document), args.path)
    if args.command == "mailbox":
        return _report(validate_mailbox(document), args.path)
    if args.command == "invocation":
        return _report(validate_invocation_receipt(document), args.path)

    errors = validate_flow(document)
    if errors:
        return _report(errors, args.path)
    if args.command == "plan":
        print(render_plan(document, args.loop))
        return 0
    if args.command == "role":
        role = next(
            (item for item in document["roles"] if item["id"] == args.role_id), None
        )
        if role is None:
            print(f"ERROR: unknown role: {args.role_id}")
            return 2
        print(json.dumps(role, indent=2, sort_keys=True))
        return 0
    try:
        driver = select_driver(document, args.role_id, set(args.tool) or None)
    except DriverSelectionError as error:
        print(f"ERROR: {error}")
        return 2
    print(json.dumps(driver, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
