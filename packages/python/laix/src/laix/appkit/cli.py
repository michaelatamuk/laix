"""Small developer CLI: explain or lint a decision JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from ..core.domain.decisions import Decision
from ..core.support.otel import decision_attributes


def _load_decision(path: str) -> Decision:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("decision"), dict):
        payload = payload["decision"]
    if not isinstance(payload, dict):
        raise ValueError("expected a decision object or a decision record")
    return Decision.from_dict(payload)


def _explain(decision: Decision, *, as_json: bool) -> str:
    if as_json:
        return json.dumps(decision_attributes(decision), indent=2, sort_keys=True)
    approval = "required" if decision.requires_approval else "not required"
    lines = [
        f"decision: {decision.decision_id or '-'}",
        f"verb: {decision.verb}",
        f"reason: {decision.reason_code}",
        f"confidence: {decision.confidence:.3f}",
        f"action: {decision.action_id or '-'}",
        f"policy: {decision.policy_version or '-'}",
        f"approval: {approval}",
        f"reversible: {decision.reversible}",
        f"trace: {decision.trace_id or '-'}",
    ]
    if decision.score is not None:
        lines.append(f"score: {decision.score:.4f}")
    if decision.supersedes:
        lines.append(f"supersedes: {decision.supersedes}")
    if decision.revision:
        lines.append(f"revision: {decision.revision}")
    lines.append(f"rationale: {decision.rationale}")
    return "\n".join(lines)


def _lint(decision: Decision) -> list[str]:
    warnings: list[str] = []
    if not decision.decision_id:
        warnings.append("missing decision_id")
    if not decision.trace_id:
        warnings.append("missing trace_id")
    if not decision.policy_version:
        warnings.append("missing policy_version")
    if decision.requires_approval and decision.verb == "act":
        warnings.append("act requires approval; the host must supply an approver")
    if decision.score is None:
        warnings.append("no score; the reason code is policy-driven")
    return warnings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="laix",
        description="Inspect LAIX decision JSON without importing the host app.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    explain = subparsers.add_parser("explain", help="print the decision fields")
    explain.add_argument("path", help="decision or decision-record JSON file")
    explain.add_argument("--json", action="store_true", help="print OpenTelemetry attributes")

    lint = subparsers.add_parser("lint", help="check a decision for missing audit fields")
    lint.add_argument("path", help="decision or decision-record JSON file")

    args = parser.parse_args(argv)
    try:
        decision = _load_decision(args.path)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"laix: {exc}", file=sys.stderr)
        return 2

    if args.command == "explain":
        print(_explain(decision, as_json=args.json))
        return 0

    warnings = _lint(decision)
    if warnings:
        for warning in warnings:
            print(f"warning: {warning}")
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
