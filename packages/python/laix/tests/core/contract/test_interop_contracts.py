"""The A2A card and OpenAPI action profile match the public contract."""

from __future__ import annotations

import json
from pathlib import Path

from laix import EXECUTION_RECEIPT_STATUSES, VERBS

ROOT = Path(__file__).resolve().parents[6]
CONTRACTS = ROOT / "packages" / "contracts"


def _load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def test_a2a_card_is_v1_and_exposes_the_decide_skill() -> None:
    card = _load("a2a-agent-card.v1.json")

    assert card["name"]
    assert card["version"]
    assert "url" not in card
    assert "protocolVersion" not in card
    interfaces = card["supportedInterfaces"]
    assert interfaces[0]["protocolVersion"] == "1.0"
    assert interfaces[0]["protocolBinding"] in {"JSONRPC", "HTTP+JSON", "GRPC"}
    assert interfaces[0]["url"].startswith("https://")
    assert "application/json" in card["defaultInputModes"]
    assert "application/json" in card["defaultOutputModes"]
    assert any(skill["id"] == "decide" for skill in card["skills"])


def test_a2a_card_parses_with_the_optional_sdk() -> None:
    try:
        from a2a.types import AgentCard
        from google.protobuf import json_format
    except ImportError:
        return
    card = _load("a2a-agent-card.v1.json")
    parsed = json_format.ParseDict(card, AgentCard())
    assert parsed.name == card["name"]
    assert len(parsed.skills) == len(card["skills"])


def test_openapi_action_profile_matches_the_receipt_contract() -> None:
    spec = _load("action.openapi.v1.json")

    assert spec["openapi"] == "3.1.0"
    operation = spec["paths"]["/actions/{action_id}"]["post"]
    assert operation["operationId"] == "executeAction"
    headers = {item["name"]: item for item in operation["parameters"]}
    assert headers["Idempotency-Key"]["required"] is True
    assert spec["x-laix-decision-verbs"] == list(VERBS)
    assert spec["x-laix-receipt-statuses"] == list(EXECUTION_RECEIPT_STATUSES)
    assert spec["x-laix-decision-schema"].endswith("/decision.v1.schema.json")

    request = spec["components"]["schemas"]["ActionExecutionRequest"]
    assert request["required"] == ["decision_id", "actor"]
    receipt = spec["components"]["schemas"]["ExecutionReceipt"]
    assert receipt["properties"]["status"]["enum"] == list(EXECUTION_RECEIPT_STATUSES)
    assert receipt["required"] == ["id", "decision_id", "action_name", "status", "actor"]


def test_openapi_action_profile_is_valid_when_the_validator_is_available() -> None:
    try:
        from openapi_spec_validator import validate
    except ImportError:
        return
    validate(_load("action.openapi.v1.json"))
