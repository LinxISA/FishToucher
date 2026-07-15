"""Command-line interface for FishToucher standards tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

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
    parser = argparse.ArgumentParser(
        prog="fishtoucher",
        description="Validate and inspect FishToucher multi-agent flow contracts.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a flow document")
    validate.add_argument("flow", type=Path)

    evidence = commands.add_parser("evidence", help="validate a gate evidence record")
    evidence.add_argument("record", type=Path)

    message = commands.add_parser("message", help="validate one agent message")
    message.add_argument("message", type=Path)

    mailbox = commands.add_parser("mailbox", help="validate an agent mailbox")
    mailbox.add_argument("mailbox", type=Path)

    invocation = commands.add_parser("invocation", help="validate an invocation receipt")
    invocation.add_argument("receipt", type=Path)

    plan = commands.add_parser("plan", help="print the deterministic stage plan")
    plan.add_argument("flow", type=Path)
    plan.add_argument("--loop", choices=("software", "architecture", "hardware"))

    commands.add_parser("schema-version", help="print the supported standard version")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "schema-version":
        print("fishtoucher.dev/v1alpha1")
        return 0

    try:
        if args.command in {"validate", "plan"}:
            document = load_json(args.flow)
        elif args.command == "evidence":
            document = load_json(args.record)
        elif args.command == "message":
            document = load_json(args.message)
        elif args.command == "invocation":
            document = load_json(args.receipt)
        else:
            document = load_mailbox(args.mailbox)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 2

    if args.command == "validate":
        return _report(validate_flow(document), args.flow)
    if args.command == "evidence":
        return _report(validate_evidence(document), args.record)
    if args.command == "message":
        return _report(validate_message(document), args.message)
    if args.command == "invocation":
        return _report(validate_invocation_receipt(document), args.receipt)
    if args.command == "mailbox":
        return _report(validate_mailbox(document), args.mailbox)

    errors = validate_flow(document)
    if errors:
        return _report(errors, args.flow)
    print(render_plan(document, args.loop))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
