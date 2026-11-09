"""The published reason-code registry and decision schema stay current."""

from __future__ import annotations

import json
import re
from pathlib import Path

from laix import REASON_CODES_VERSION, Decision, reason_code_registry
from laix.decision.engines.sensing.signals.gates.reason import REASONS
from laix.decision.schema import build_schema, check

ROOT = Path(__file__).resolve().parents[6]
CONTRACTS = ROOT / "packages" / "contracts"


def test_registry_matches_signal_attention_enum() -> None:
    registry = reason_code_registry()

    assert registry["version"] == REASON_CODES_VERSION
    assert registry["groups"]["signal_attention"] == list(REASONS)
    assert registry["codes"] == sorted(set(registry["codes"]))
    assert registry["extensible"] is True


def test_registry_file_is_current() -> None:
    committed = json.loads((CONTRACTS / "reason-codes.v1.json").read_text(encoding="utf-8"))
    assert committed == reason_code_registry()


def test_decision_schema_file_is_current() -> None:
    definition = build_schema()["$defs"]["Decision"]
    definition["title"] = "LAIX Decision v1"
    definition["description"] = (
        "The public decision shape returned by decide, DecisionClient and every policy."
    )
    expected = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://laix.dev/contracts/decision.v1.schema.json",
        **definition,
    }
    committed = json.loads((CONTRACTS / "decision.v1.schema.json").read_text(encoding="utf-8"))
    assert committed == expected

    decision = Decision(
        verb="act",
        confidence=0.9,
        reason_code="safe_action",
        rationale="inside the limit",
        decision_id="DEC-1",
    )
    assert check("Decision", decision.to_dict()) == []


def test_every_literal_source_reason_code_is_registered() -> None:
    known = set(reason_code_registry()["codes"])
    missing: set[str] = set()

    for path in (ROOT / "packages" / "python" / "laix" / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r'reason_code\s*=\s*"([a-z_]+)"', text):
            if match.group(1) not in known:
                missing.add(match.group(1))
        for match in re.finditer(r'_wait\(\s*"([a-z_]+)"', text):
            if match.group(1) not in known:
                missing.add(match.group(1))

    for path in (ROOT / "packages" / "typescript" / "laix" / "src").rglob("*.ts"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r'reasonCode:\s*"([a-z_]+)"', text):
            if match.group(1) not in known:
                missing.add(match.group(1))

    assert missing == set()
