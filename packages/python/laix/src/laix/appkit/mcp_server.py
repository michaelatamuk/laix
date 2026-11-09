"""Optional MCP stdio server exposing the LAIX decision contract.

Install the optional dependency and run:

    python -m pip install "laix[mcp]"
    laix-mcp

The server exposes one tool, ``decide``. It accepts the public request JSON and
returns the same decision objects as ``decide``.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from ..decision.contract.planner_policy import PlannerPolicy
from ..decision.dispatch import decide
from ..decision.domain.decisions import (
    ActionOption,
    Belief,
    Constraint,
    DecisionRequest,
    Goal,
    Intent,
    Observation,
    Situation,
)
from ..decision.engines.decision.single.planners.composite.live_composite_planner import (
    LiveCompositePlanner,
)
from ..decision.engines.sensing.signals.input import Signal, SignalContext, SignalFeedback
from ..decision.support.serialize import to_primitive
from ..decision.support.time import parse_iso
from ..decision.support.version import SCHEMA_VERSION

try:
    from mcp.server.mcpserver import MCPServer as _MCPServer
except ImportError:  # pragma: no cover - optional dependency
    _MCPServer = None


def _require_mcp() -> None:
    if _MCPServer is None:
        raise RuntimeError(
            'the MCP server needs the optional dependency: pip install "laix[mcp]"'
        )


def _situation(payload: dict[str, Any], *, subject: str, at: str) -> Situation:
    data = dict(payload)
    data.setdefault("id", "situation-1")
    data.setdefault("at", at)
    data.setdefault("subject", subject)
    data["observations"] = tuple(
        item if isinstance(item, Observation) else Observation(**item)
        for item in data.get("observations", ())
    )
    data["beliefs"] = tuple(
        item if isinstance(item, Belief) else Belief.from_dict(item)
        for item in data.get("beliefs", ())
    )
    data["goals"] = tuple(
        item if isinstance(item, Goal) else Goal(**item)
        for item in data.get("goals", ())
    )
    data["constraints"] = tuple(
        item if isinstance(item, Constraint) else Constraint(**item)
        for item in data.get("constraints", ())
    )
    data["attributes"] = dict(data.get("attributes", {}))
    return Situation(**data)


def _signal(payload: dict[str, Any]) -> Signal:
    data = dict(payload)
    data["evidence_refs"] = tuple(str(item) for item in data.get("evidence_refs", ()))
    for key in ("intent", "handover"):
        value = data.get(key)
        if isinstance(value, dict):
            data[key] = Intent(**value)
    return Signal(**data)


def _context(payload: dict[str, Any]) -> SignalContext:
    data = dict(payload)
    now = data.get("now")
    if isinstance(now, str):
        now = parse_iso(now)
    if now is None:
        raise ValueError("context.now is required")
    data["now"] = now
    quiet = data.get("quiet_hours")
    if quiet is not None:
        data["quiet_hours"] = tuple(quiet)
    data["muted_kinds"] = tuple(str(item) for item in data.get("muted_kinds", ()))
    data["sent"] = frozenset(str(item) for item in data.get("sent", ()))
    data["feedback"] = {
        str(key): value if isinstance(value, SignalFeedback) else SignalFeedback(**value)
        for key, value in data.get("feedback", {}).items()
    }
    data["learned"] = dict(data.get("learned", {}))
    return SignalContext(**data)


def parse_request(payload: dict[str, Any]) -> DecisionRequest:
    """Build a ``DecisionRequest`` from its public JSON shape."""
    if not isinstance(payload, dict):
        raise ValueError("request must be an object")
    subject = str(payload.get("subject") or "").strip()
    at = str(payload.get("at") or "").strip()
    if not subject:
        raise ValueError("request.subject is required")
    if not at:
        raise ValueError("request.at is required")

    situation_payload = payload.get("situation")
    situation = (
        _situation(situation_payload, subject=subject, at=at)
        if isinstance(situation_payload, dict)
        else None
    )
    options = tuple(
        item if isinstance(item, ActionOption) else ActionOption.from_dict(item)
        for item in payload.get("options", ())
    )
    signals = tuple(
        item if isinstance(item, Signal) else _signal(item)
        for item in payload.get("signals", ())
    )
    context_payload = payload.get("context")
    context = _context(context_payload) if isinstance(context_payload, dict) else None
    recipients = tuple(str(item) for item in payload.get("recipients", ()))

    return DecisionRequest(
        subject=subject,
        at=at,
        signals=signals,
        context=context,
        situation=situation,
        options=options,
        attributes=dict(payload.get("attributes", {})),
        confidence=payload.get("confidence"),
        confidence_source=str(payload.get("confidence_source", "")),
        calibrated=bool(payload.get("calibrated", False)),
        deadline=payload.get("deadline"),
        valid_until=payload.get("valid_until"),
        event_id=str(payload.get("event_id", "")),
        target=str(payload.get("target", "one")),
        recipients=recipients,
    )


def decide_tool(request: dict[str, Any], policy: str = "auto") -> str:
    """MCP tool: answer one decision request and return the decision JSON."""
    parsed = parse_request(request)
    if policy == "auto":
        decisions = decide(parsed)
    elif policy == "live":
        decisions = decide(parsed, policy=PlannerPolicy(LiveCompositePlanner()))
    else:
        raise ValueError("policy must be 'auto' or 'live'")
    return json.dumps(
        {"decisions": [to_primitive(item.to_dict()) for item in decisions]},
        indent=2,
        ensure_ascii=False,
    )


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("laix")
    except Exception:  # pragma: no cover - source checkout without metadata
        return SCHEMA_VERSION


def build_server() -> Any:
    """Build the MCP server. Import fails clearly when ``mcp`` is not installed."""
    _require_mcp()
    server = _MCPServer(
        name="laix",
        title="LAIX decisions",
        description="The decision layer for AI agents.",
        version=_version(),
    )
    server.add_tool(
        decide_tool,
        name="decide",
        title="Decide",
        description=(
            "Answer one LAIX decision request. Pass the public DecisionRequest JSON in "
            "`request`. Use `policy: auto` for decision dispatch or `policy: live` for the "
            "live composite planner. The result is a JSON array of Decision objects."
        ),
        structured_output=False,
    )
    return server


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="laix-mcp",
        description="Run the LAIX MCP server over stdio.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio",),
        default="stdio",
        help="MCP transport (stdio only).",
    )
    args = parser.parse_args(argv)
    try:
        server = build_server()
    except RuntimeError as exc:
        print(f"laix-mcp: {exc}", file=sys.stderr)
        return 2
    server.run(args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
