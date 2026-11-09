"""The contract: behaviour, determinism and isolation of laix_attention."""

from __future__ import annotations

import ast
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import laix.decision.sensing.signals as laix
import laix.decision.evaluation.cases as evaluation_pkg
from laix.decision.domain.outcomes.signal_attention import (
    HELPED,
    HURT,
    NEUTRAL,
    UNKNOWN,
    SignalAttentionOutcome,
    SignalAttentionLog,
    label_for_feedback,
    result_for_reason,
)
from laix.decision.sensing.signals import (
    SignalContext,
    Signal,
    decide_signal_attention,
    dedupe_key,
    is_quiet,
    rollup,
)
from laix.decision.evaluation.cases.signal_attention import (
    benchmark,
    compare,
    load_vectors,
    precision_recall,
    run_vectors,
    validate_document,
)

PACKAGE = Path(laix.__file__).resolve().parent
VECTORS = load_vectors(PACKAGE / "signal-attention.v1.json")
TZ = timezone(timedelta(hours=2))


def at(hour: int, minute: int = 0, day: int = 1) -> datetime:
    return datetime(2026, 11, day, hour, minute, tzinfo=TZ)


def test_every_contract_vector_passes() -> None:
    problems = run_vectors(VECTORS)
    assert problems == []
    assert len(VECTORS["cases"]) >= 20


def test_contract_version_is_declared() -> None:
    assert VECTORS["version"] == laix.__version__


def test_decisions_keep_input_order_and_identity() -> None:
    signals = [Signal(id=f"s-{i}", kind="k", severity="high", confidence=0.9) for i in range(3)]
    decisions = decide_signal_attention(signals, SignalContext(now=at(10), quiet_hours=None))
    assert [d.signal_id for d in decisions] == ["s-0", "s-1", "s-2"]
    assert all(d.verb == "guide" for d in decisions)


def test_trace_ids_are_stable_and_distinct_per_action() -> None:
    signal = Signal(id="s-1", kind="k", severity="high", confidence=0.9)
    first = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None))[0]
    second = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None))[0]
    assert first.trace_id == second.trace_id
    assert first.trace_id.startswith("tr-") and len(first.trace_id) == 15


def test_score_breakdown_adds_up() -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.5, due=at(12).isoformat(), interruption_cost=0.5)
    decision = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None))[0]
    breakdown = decision.breakdown
    assert breakdown.total == pytest.approx(
        breakdown.severity + breakdown.due + breakdown.confidence + breakdown.interruption + breakdown.learned
    )
    assert decision.score == pytest.approx(breakdown.total)


def test_dedupe_key_is_signal_and_day() -> None:
    signal = Signal(id="D-123", kind="k")
    assert dedupe_key(signal, at(23, 59)) == "D-123:2026-11-01"
    assert dedupe_key(signal, at(0, 1, day=2)) == "D-123:2026-11-02"


@pytest.mark.parametrize(
    "hour,minute,expected",
    [(21, 59, False), (22, 0, True), (23, 59, True), (0, 0, True), (6, 0, True), (6, 1, False), (12, 0, False)],
)
def test_quiet_hours_are_inclusive(hour: int, minute: int, expected: bool) -> None:
    assert is_quiet(at(hour, minute), ("22:00", "06:00")) is expected


def test_bad_quiet_hours_are_never_quiet() -> None:
    assert is_quiet(at(23), "not-a-window") is False
    assert is_quiet(at(23), None) is False


def test_rollup_orders_by_severity_then_due() -> None:
    signals = [
        Signal(id="low", kind="k", severity="low", due="2026-11-02"),
        Signal(id="critical-late", kind="k", severity="critical", due="2026-11-09"),
        Signal(id="critical-soon", kind="k", severity="critical", due="2026-11-03"),
    ]
    assert [s.id for s in rollup(signals)] == ["critical-soon", "critical-late", "low"]


def test_outcome_log_precision_needs_evidence() -> None:
    log = SignalAttentionLog()
    assert log.precision() is None
    log.record(SignalAttentionOutcome("a", "kind-a", "guide", HELPED, score=80))
    log.record(SignalAttentionOutcome("b", "kind-a", "guide", HURT, reason_code="false_alarm", score=70))
    log.record(SignalAttentionOutcome("c", "kind-b", "guide", NEUTRAL, reason_code="design_change", score=40))
    assert log.precision() == pytest.approx(1 / 3)
    assert log.hazard_rate() == pytest.approx(1 / 3)
    assert log.precision("kind-a") == pytest.approx(0.5)
    assert log.adjustment("kind-a") == pytest.approx(0.0)


def test_reason_codes_map_to_labels() -> None:
    assert result_for_reason("false_alarm") == HURT
    assert result_for_reason("data_error") == HURT
    assert result_for_reason("design_change") == NEUTRAL
    assert result_for_reason("no_action") == NEUTRAL
    assert result_for_reason(None) == UNKNOWN
    assert label_for_feedback("accepted") == HELPED
    assert label_for_feedback("dismissed", "false_alarm") == HURT


def test_calibration_has_one_row_per_bucket() -> None:
    log = SignalAttentionLog()
    log.record(SignalAttentionOutcome("a", "k", "guide", HELPED, score=10))
    log.record(SignalAttentionOutcome("b", "k", "guide", HURT, score=90))
    rows = log.calibration()
    assert len(rows) == 4
    assert rows[0]["n"] == 1 and rows[0]["rate"] == 1.0
    assert rows[3]["n"] == 1 and rows[3]["rate"] == 0.0


def test_precision_recall_is_generic() -> None:
    result = precision_recall({"a", "b"}, {"b", "c"})
    assert result == {"detected": 2, "known": 2, "matched": 1, "precision": 0.5, "recall": 0.5}
    assert precision_recall([], [])["precision"] == 1.0


def test_compare_reports_a_mismatch() -> None:
    case = {
        "id": "tampered",
        "context": {"now": "2026-11-01T10:00:00+02:00", "quietHours": None},
        "signals": [{"id": "s", "kind": "k", "severity": "high", "confidence": 0.9}],
        "expected": [{"signalId": "s", "action": "wait", "reason": "no", "deliver": False, "record": False, "score": 1}],
    }
    problems = compare(case)
    assert problems and "tampered" in problems[0]


#: No file may read the clock directly; time comes in SignalContext.now.
CLOCK_ALLOWED: set[str] = set()
LOCAL_PACKAGES = {"laix"}


def guard_violations(root: Path) -> list[str]:
    """Everything that would couple this policy to a clock or a third-party package."""
    problems: list[str] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name not in CLOCK_ALLOWED and "datetime.now(" in text:
            problems.append(f"{path.name}: reads the clock directly")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules = [node.module.split(".")[0]]
            for module in modules:
                if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES:
                    problems.append(f"{path.name}: imports {module}")
    return problems


def test_the_policy_uses_only_the_standard_library() -> None:
    assert guard_violations(PACKAGE) == []


def test_the_guard_catches_a_third_party_import(tmp_path: Path) -> None:
    module = tmp_path / "laix_attention"
    module.mkdir()
    (module / "__init__.py").write_text("import fastapi\n", encoding="utf-8")
    assert any("imports fastapi" in problem for problem in guard_violations(module))


def test_the_guard_catches_a_direct_clock_read(tmp_path: Path) -> None:
    module = tmp_path / "laix_attention"
    module.mkdir()
    (module / "now.py").write_text("from datetime import datetime\nVALUE = datetime.now()\n", encoding="utf-8")
    assert any("reads the clock" in problem for problem in guard_violations(module))


def test_the_contract_file_ships_with_the_package() -> None:
    assert (PACKAGE / "signal-attention.v1.json").is_file()
    assert (Path(evaluation_pkg.__file__).resolve().parent / "signal-attention-bench.v1.json").is_file()


# --------------------------------------------------------------------------- feedback


def test_a_snooze_holds_until_it_expires() -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.9)
    future = SignalContext(now=at(10), quiet_hours=None, feedback={"s": laix.SignalFeedback("snoozed", until="2026-11-02T08:00:00+02:00")})
    past = SignalContext(now=at(10), quiet_hours=None, feedback={"s": laix.SignalFeedback("snoozed", until="2026-10-31T08:00:00+02:00")})
    assert decide_signal_attention([signal], future)[0].reason_code == "snoozed"
    assert decide_signal_attention([signal], past)[0].verb == "guide"


def test_a_snooze_without_an_expiry_stays_closed() -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.9)
    context = SignalContext(now=at(10), quiet_hours=None, feedback={"s": laix.SignalFeedback("snoozed")})
    assert decide_signal_attention([signal], context)[0].reason_code == "snoozed"


@pytest.mark.parametrize("state,reason", [("wrong", "wrong"), ("assigned", "assigned"), ("dismissed", "dismissed")])
def test_negative_feedback_suppresses(state: str, reason: str) -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.9)
    context = SignalContext(now=at(10), quiet_hours=None, feedback={"s": laix.SignalFeedback(state)})
    decision = decide_signal_attention([signal], context)[0]
    assert (decision.verb, decision.reason_code, decision.record) == ("wait", reason, False)


def test_accepted_feedback_does_not_suppress() -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.9)
    context = SignalContext(now=at(10), quiet_hours=None, feedback={"s": laix.SignalFeedback("accepted")})
    assert decide_signal_attention([signal], context)[0].verb == "guide"


# --------------------------------------------------------------------------- execution seam


def intent_signal(**overrides) -> Signal:
    base = {
        "id": "s",
        "kind": "k",
        "severity": "high",
        "confidence": 0.9,
        "intent": laix.Intent("apply_variant", {"v": "b"}),
        "reversible": True,
    }
    base.update(overrides)
    return Signal(**base)


def test_act_needs_an_explicit_opt_in() -> None:
    signal = intent_signal()
    off = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None))[0]
    on = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None, allow_act=True))[0]
    assert (off.verb, off.intent) == ("guide", None)
    assert on.verb == "act" and on.intent is not None and on.intent.capability == "apply_variant"


def test_an_irreversible_intent_is_only_notified() -> None:
    signal = intent_signal(reversible=False)
    decision = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None, allow_act=True))[0]
    assert decision.verb == "guide"


def test_approval_keeps_the_act_flag() -> None:
    signal = intent_signal(requires_approval=True)
    decision = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None, allow_act=True))[0]
    assert (decision.verb, decision.reason_code, decision.requires_approval) == ("act", "act", True)


def test_a_blocked_signal_never_acts() -> None:
    signal = intent_signal()
    context = SignalContext(now=at(23, 30), quiet_hours=("22:00", "06:00"), allow_act=True)
    assert decide_signal_attention([signal], context)[0].verb == "wait"


def test_escalation_is_carried_only_when_escalating() -> None:
    signal = intent_signal(
        severity="critical",
        requires_approval=False,
        intent=None,
        reversible=False,
        handover=laix.Intent("handover", {"target": "target-a", "reason": "overdue"}),
    )
    context = SignalContext(now=at(10), quiet_hours=None, escalate_after_hours=24)
    decision = decide_signal_attention([signal], context)[0]
    assert decision.verb == "guide" and decision.intent is None

    overdue = {"due": "2026-10-30T10:00:00+02:00"}
    signal = intent_signal(severity="critical", intent=None, reversible=False, handover=laix.Intent("handover", {"target": "target-a", "reason": "overdue"}), **overdue)
    decision = decide_signal_attention([signal], context)[0]
    assert decision.verb == "escalate" and decision.intent is not None
    assert decision.intent.capability == "handover" and decision.intent.args["target"] == "target-a"


# --------------------------------------------------------------------------- cost and undo


def test_cost_of_waiting_scales_with_deadline_and_severity() -> None:
    critical = Signal(id="a", kind="k", severity="critical", due="2026-11-02T09:00:00+02:00")
    high = Signal(id="b", kind="k", severity="high", due="2026-11-02T09:00:00+02:00")
    distant = Signal(id="c", kind="k", severity="critical", due="2026-12-01T09:00:00+02:00")
    none = Signal(id="d", kind="k", severity="critical")
    context = SignalContext(now=at(10), quiet_hours=None)
    assert laix.cost_of_waiting(critical, context) == pytest.approx(40.0)
    assert laix.cost_of_waiting(high, context) == pytest.approx(30.0)
    assert laix.cost_of_waiting(distant, context) == 0.0
    assert laix.cost_of_waiting(none, context) == 0.0


def test_undo_hint_matches_the_action() -> None:
    assert laix.undo_hint("guide", False) == "withdraw"
    assert laix.undo_hint("ask", False) == "withdraw"
    assert laix.undo_hint("act", True) == "cancel"
    assert laix.undo_hint("act", False) is None
    assert laix.undo_hint("wait", True) is None
    assert laix.undo_hint("escalate", True) is None


def test_every_decision_carries_cost_and_undo() -> None:
    signal = Signal(id="s", kind="k", severity="high", confidence=0.9, due="2026-11-02T09:00:00+02:00")
    decision = decide_signal_attention([signal], SignalContext(now=at(10), quiet_hours=None))[0]
    assert decision.cost_of_waiting > 0
    assert decision.undo_hint == "withdraw"
    assert decision.as_dict()["cost_of_waiting"] == round(decision.cost_of_waiting, 2)


# --------------------------------------------------------------------------- schema and bench


def test_validate_document_accepts_the_contract() -> None:
    assert validate_document(VECTORS) == []


def test_validate_document_rejects_an_invented_verb() -> None:
    broken = {
        "contract": "laix",
        "version": "1.1.0",
        "cases": [
            {
                "id": "broken",
                "context": {"now": "2026-11-01T10:00:00+02:00"},
                "signals": [{"id": "s", "kind": "k", "severity": "high"}],
                "expected": [{"verb": "notify_now", "reason_code": "worth_surfacing", "deliver": True, "record": True, "score": 1}],
            }
        ],
    }
    problems = validate_document(broken)
    assert any("unknown verb" in problem for problem in problems)


def test_the_bench_beats_both_baselines() -> None:
    document = load_vectors(Path(evaluation_pkg.__file__).resolve().parent / "signal-attention-bench.v1.json")
    result = benchmark(document)
    rows = result["rows"]
    assert result["cases"] == 12
    assert rows["policy"]["precision"] > rows["severity_only"]["precision"]
    assert rows["policy"]["precision"] > rows["always_notify"]["precision"]
    assert rows["policy"]["hazard"] == 0.0
    assert rows["always_notify"]["recall"] == 1.0
    assert rows["policy"]["missed_helpful"] >= 1
    assert rows["always_notify"]["raised"] == 12
