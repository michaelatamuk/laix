"""Decision timeline: formal semantics for decisions over event time.

A timeline is an append-only set of decisions that enforces the revision rules:
a root has revision 0 and no predecessor; a revision points to the decision it
supersedes, has the next revision number, and does not move backwards in event
time. The timeline also reports chains, superseded decisions and late events.
"""

from __future__ import annotations

from typing import Iterable

from ...decision.domain.decisions import Decision
from .timeline_error import TimelineError
from .timeline_report import TimelineReport


class DecisionTimeline:
    """An append-only timeline with revision and event-time rules."""

    def __init__(self, decisions: Iterable[Decision] = ()) -> None:
        self._by_id: dict[str, Decision] = {}
        self._order: list[str] = []
        for decision in decisions:
            self.add(decision)

    def add(self, decision: Decision) -> Decision:
        """Append one decision or raise ``TimelineError``."""
        decision_id = decision.decision_id
        if not decision_id:
            raise TimelineError("decision id is required")
        if decision_id in self._by_id:
            raise TimelineError(f"duplicate decision id: {decision_id}")

        revision = decision.revision
        previous_id = decision.supersedes
        if revision < 0:
            raise TimelineError(f"negative revision: {decision_id}")
        if revision == 0 and previous_id:
            raise TimelineError(
                f"root decision {decision_id} cannot supersede {previous_id}"
            )
        if revision > 0:
            if not previous_id:
                raise TimelineError(
                    f"revision {revision} of {decision_id} needs a predecessor"
                )
            previous = self._by_id.get(previous_id)
            if previous is None:
                raise TimelineError(
                    f"unknown predecessor {previous_id} for {decision_id}"
                )
            if previous.revision + 1 != revision:
                raise TimelineError(
                    f"revision {revision} of {decision_id} must follow "
                    f"{previous.revision}"
                )
            if (
                previous.stream_id
                and decision.stream_id
                and previous.stream_id != decision.stream_id
            ):
                raise TimelineError(
                    f"stream mismatch: {previous.stream_id} -> {decision.stream_id}"
                )
            if (
                previous.event_time
                and decision.event_time
                and decision.event_time < previous.event_time
            ):
                raise TimelineError(
                    f"event time moved backwards: {previous.event_time} -> "
                    f"{decision.event_time}"
                )

        self._by_id[decision_id] = decision
        self._order.append(decision_id)
        return decision

    def get(self, decision_id: str) -> Decision:
        try:
            return self._by_id[decision_id]
        except KeyError as error:
            raise TimelineError(f"unknown decision: {decision_id}") from error

    def all(self) -> tuple[Decision, ...]:
        return tuple(self._by_id[item] for item in self._order)

    def history(self, decision_id: str) -> tuple[Decision, ...]:
        """Return the chain from the root to ``decision_id``."""
        chain: list[Decision] = []
        seen: set[str] = set()
        current: str | None = decision_id
        while current is not None:
            if current in seen:
                raise TimelineError(f"cycle at {current}")
            seen.add(current)
            decision = self.get(current)
            chain.append(decision)
            current = decision.supersedes
        chain.reverse()
        return tuple(chain)

    def superseded_ids(self) -> frozenset[str]:
        return frozenset(
            decision.supersedes
            for decision in self._by_id.values()
            if decision.supersedes
        )

    def is_superseded(self, decision_id: str) -> bool:
        return decision_id in self.superseded_ids()

    def current(self, stream_id: str | None = None) -> tuple[Decision, ...]:
        """Return the latest decision in each chain."""
        superseded = self.superseded_ids()
        latest: dict[str, Decision] = {}
        for decision in self.all():
            if decision.decision_id in superseded:
                continue
            if stream_id is not None and decision.stream_id != stream_id:
                continue
            latest[decision.decision_id] = decision
        return tuple(latest.values())

    def latest(self, stream_id: str | None = None) -> Decision | None:
        """Return the last appended decision, optionally for one stream."""
        for decision_id in reversed(self._order):
            decision = self._by_id[decision_id]
            if stream_id is None or decision.stream_id == stream_id:
                return decision
        return None

    def late(self, watermark: str) -> tuple[Decision, ...]:
        """Return decisions whose event time is before ``watermark``."""
        return tuple(
            decision
            for decision in self.all()
            if decision.event_time is not None and decision.event_time < watermark
        )

    def issues(self) -> tuple[str, ...]:
        """Re-check stored decisions and return every issue found."""
        issues: list[str] = []
        for decision in self.all():
            if not decision.decision_id:
                issues.append("decision id is required")
                continue
            if decision.revision == 0:
                if decision.supersedes:
                    issues.append(
                        f"root {decision.decision_id} supersedes "
                        f"{decision.supersedes}"
                    )
                continue
            previous = self._by_id.get(decision.supersedes or "")
            if previous is None:
                issues.append(
                    f"missing predecessor {decision.supersedes} for "
                    f"{decision.decision_id}"
                )
                continue
            if previous.revision + 1 != decision.revision:
                issues.append(
                    f"revision gap {previous.revision} -> {decision.revision} "
                    f"at {decision.decision_id}"
                )
            if (
                previous.stream_id
                and decision.stream_id
                and previous.stream_id != decision.stream_id
            ):
                issues.append(
                    f"stream mismatch at {decision.decision_id}: "
                    f"{previous.stream_id} -> {decision.stream_id}"
                )
            if (
                previous.event_time
                and decision.event_time
                and decision.event_time < previous.event_time
            ):
                issues.append(f"event time backwards at {decision.decision_id}")
        return tuple(issues)

    def assert_valid(self) -> None:
        issues = self.issues()
        if issues:
            raise TimelineError("; ".join(issues))

    def report(self) -> TimelineReport:
        superseded = self.superseded_ids()
        roots = [
            decision
            for decision in self.all()
            if decision.decision_id not in superseded
        ]
        return TimelineReport(
            decisions=len(self._by_id),
            chains=len(roots),
            superseded=len(superseded),
            issues=self.issues(),
        )

    def to_dict(self) -> dict[str, object]:
        return {"decisions": [decision.to_dict() for decision in self.all()]}

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "DecisionTimeline":
        decisions = payload.get("decisions", ())
        return cls(
            Decision.from_dict(item)
            for item in decisions
            if isinstance(item, dict)
        )


__all__ = ["DecisionTimeline", "TimelineError", "TimelineReport"]
