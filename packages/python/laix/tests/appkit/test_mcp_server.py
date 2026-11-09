"""The optional MCP server exposes the decision contract."""

from __future__ import annotations

import asyncio
import json

import pytest

pytest.importorskip("mcp")

from laix.appkit.mcp_server import build_server, decide_tool, parse_request


def signal_request() -> dict:
    return {
        "subject": "bill",
        "at": "2026-11-01T10:00:00Z",
        "signals": [
            {
                "id": "s-1",
                "kind": "deadline",
                "severity": "high",
                "confidence": 0.9,
            }
        ],
        "context": {"now": "2026-11-01T10:00:00Z", "quiet_hours": None},
    }


def action_request() -> dict:
    at = "2026-11-01T10:00:00Z"
    return {
        "subject": "leaking sink",
        "at": at,
        "situation": {
            "id": "situation-1",
            "at": at,
            "subject": "leaking sink",
            "beliefs": [
                {
                    "id": "b-1",
                    "proposition": "water is leaking",
                    "confidence": 0.9,
                }
            ],
        },
        "options": [
            {
                "id": "valve",
                "verb": "act",
                "name": "close the valve",
                "expected_benefit": 0.9,
                "risk": 0.1,
            }
        ],
    }


def test_parse_request_builds_the_core_shapes() -> None:
    request = parse_request(signal_request())

    assert request.subject == "bill"
    assert request.signals[0].id == "s-1"
    assert request.context is not None
    assert request.context.now.year == 2026


def test_decide_tool_returns_signal_attention() -> None:
    payload = json.loads(decide_tool(signal_request()))

    assert payload["decisions"][0]["verb"] == "guide"
    assert payload["decisions"][0]["reason_code"] == "worth_surfacing"


def test_decide_tool_returns_an_action() -> None:
    payload = json.loads(decide_tool(action_request()))

    assert payload["decisions"][0]["verb"] == "act"
    assert payload["decisions"][0]["action_id"] == "valve"


def test_decide_tool_accepts_the_live_policy() -> None:
    payload = json.loads(decide_tool(action_request(), policy="live"))

    assert payload["decisions"][0]["verb"] == "act"
    assert payload["decisions"][0]["action_id"] == "valve"


def test_decide_tool_rejects_an_unknown_policy() -> None:
    with pytest.raises(ValueError, match="policy"):
        decide_tool(action_request(), policy="unknown")


def test_server_lists_and_calls_the_decide_tool() -> None:
    server = build_server()

    tools = asyncio.run(server.list_tools())
    assert [tool.name for tool in tools] == ["decide"]
    assert "request" in tools[0].input_schema["properties"]

    result = asyncio.run(
        server.call_tool("decide", {"request": signal_request()})
    )
    payload = json.loads(result.content[0].text)
    assert payload["decisions"][0]["verb"] == "guide"
