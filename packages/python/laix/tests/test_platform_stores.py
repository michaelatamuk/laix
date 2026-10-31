"""Platform, state-store and outcome-store contracts."""

from __future__ import annotations

from laix import (
    ApprovalDecision,
    ApprovalRequest,
    Capability,
    ExperienceState,
    InMemoryPlatform,
    InMemoryStateStore,
    Outcome,
    OutcomeLedger,
    SkillCall,
)


def test_platform_runs_skills_and_streams_events() -> None:
    platform = InMemoryPlatform()
    platform.register("lookup", lambda call: {"echo": call.args.get("value")})
    call = SkillCall("lookup", {"value": 7}, trace_id="tr-1")
    assert platform.run_skill(call) == {"echo": 7}
    kinds = [event.kind for event in platform.events("tr-1")]
    assert kinds == ["skill.started", "skill.finished"]


def test_platform_cancel_and_state() -> None:
    platform = InMemoryPlatform()
    assert platform.cancel("run-1", "changed") is True
    platform.write_state("show", {"id": "show-1"})
    assert platform.read_state("show") == {"id": "show-1"}
    assert platform.read_state("missing") is None


def test_platform_approval_and_capability() -> None:
    platform = InMemoryPlatform(
        approver=lambda request: ApprovalDecision(approved=True, by="owner", note="ok")
    )
    decision = platform.request_approval(ApprovalRequest(decision_id="d-1", action="assign"))
    assert decision.approved is True
    assert decision.by == "owner"
    assert platform.capability("fast").level == "fast"
    assert isinstance(platform.capability("deep"), Capability)


def test_state_store_save_load_delete() -> None:
    store = InMemoryStateStore()
    state = ExperienceState(subject="one", phase="decide")
    store.save("key", state)
    assert store.load("key") is state
    store.delete("key")
    assert store.load("key") is None


def test_outcome_store_add_and_summary() -> None:
    ledger = OutcomeLedger()
    outcome = Outcome(
        id="o-1",
        decision_id="d-1",
        metric="time",
        before=10.0,
        after=8.0,
        delta=-2.0,
        label="helped",
        attributed=True,
        direction="lower-better",
    )
    assert ledger.add(outcome) is outcome
    assert ledger.all() == [outcome]
    assert ledger.for_decision("d-1") == [outcome]
    assert ledger.summary()["helped"] == 1
