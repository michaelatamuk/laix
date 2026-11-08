"""Developer CLI: explain and lint decision JSON."""

from __future__ import annotations

import json

from laix import Decision
from laix.appkit.cli import main


def _write(tmp_path, decision: Decision, *, record: bool = False):
    payload = decision.to_dict()
    if record:
        payload = {"id": "rec-1", "decision": payload}
    path = tmp_path / "decision.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_explain_prints_the_decision(tmp_path, capsys) -> None:
    decision = Decision(
        verb="act",
        confidence=0.9,
        reason_code="safe_action",
        rationale="inside the limit",
        decision_id="DEC-1",
        trace_id="TRC-1",
        policy_version="live.v1",
        action_id="valve",
        score=0.91,
    )
    path = _write(tmp_path, decision)

    assert main(["explain", str(path)]) == 0
    output = capsys.readouterr().out
    assert "decision: DEC-1" in output
    assert "verb: act" in output
    assert "reason: safe_action" in output
    assert "action: valve" in output
    assert "score: 0.9100" in output


def test_explain_reads_a_decision_record(tmp_path, capsys) -> None:
    decision = Decision(
        verb="wait",
        confidence=0.5,
        reason_code="no_options",
        rationale="nothing to do",
        decision_id="DEC-2",
    )
    path = _write(tmp_path, decision, record=True)

    assert main(["explain", str(path)]) == 0
    assert "decision: DEC-2" in capsys.readouterr().out


def test_explain_json_prints_otel_attributes(tmp_path, capsys) -> None:
    decision = Decision(
        verb="act",
        confidence=0.9,
        reason_code="safe_action",
        rationale="inside the limit",
        decision_id="DEC-1",
    )
    path = _write(tmp_path, decision)

    assert main(["explain", "--json", str(path)]) == 0
    attributes = json.loads(capsys.readouterr().out)
    assert attributes["laix.decision.id"] == "DEC-1"
    assert attributes["laix.verb"] == "act"


def test_lint_reports_missing_audit_fields(tmp_path, capsys) -> None:
    decision = Decision(
        verb="wait",
        confidence=0.5,
        reason_code="no_options",
        rationale="nothing to do",
    )
    path = _write(tmp_path, decision)

    assert main(["lint", str(path)]) == 1
    output = capsys.readouterr().out
    assert "missing decision_id" in output
    assert "missing trace_id" in output
    assert "missing policy_version" in output
