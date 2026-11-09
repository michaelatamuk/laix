"""Streaming decisions: a session, event time, cadence, backpressure and revisions.

The decision layer's ``decide`` is stateless.  A stream session owns the state a live loop
needs: an event-time watermark, a cooldown between decisions, a bounded buffer
with an explicit overflow policy, and revisions that supersede an earlier
decision.  It returns decisions synchronously and exposes the same decisions as
an async iterator for the host's loop.
"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict, deque
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Callable, Iterable, Sequence

from ...decision.domain.decisions import DECISION_STATUSES, Decision, DecisionRequest, Trace
from ...decision.planners.single.human_attention.human_attention_planner import HumanAttentionBudget
from ...decision.support.ids import new_id
from ...decision.support.time import parse_iso, utcnow
from .checkpoint import StreamCheckpointStore
from .feed import FeedMixin, Refiner
from .manual_clock import ManualClock
from .stream_stats import StreamStats
from .timeline import DecisionTimeline

Decider = Callable[[DecisionRequest], Sequence[Decision]]
Clock = Callable[[], datetime]
Recorder = Callable[[Decision], None]

FULL_POLICIES = ("latest_wins", "drop_oldest", "drop_newest")
"""What to do when the bounded buffer is full."""

LATE_POLICIES = ("drop", "accept")
"""What to do with an event whose event time is behind the watermark."""


class StreamSession(FeedMixin):
    """One live decision stream.

    ``decide`` is any callable with the decision contract: one ``DecisionRequest``
    in, a sequence of ``Decision`` objects out.  ``observe`` admits an event,
    applies event-time and cooldown rules, stamps the stream fields and buffers
    the result.  ``decisions`` drains that buffer from an async loop.  Call
    ``observe`` from the same event loop that consumes ``decisions``.
    """

    def __init__(
        self,
        decide: Decider,
        *,
        stream_id: str = "",
        capacity: int = 32,
        on_full: str = "latest_wins",
        late: str = "drop",
        cooldown_ms: int = 0,
        hysteresis_ms: int = 0,
        dedupe_ms: int = 0,
        max_decisions_per_window: int | None = None,
        budget_window_ms: int = 1000,
        latency_samples: int = 256,
        trace: bool = True,
        recorder: Recorder | None = None,
        timeline: DecisionTimeline | None = None,
        human_attention_budget: HumanAttentionBudget | None = None,
        clock: Clock | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if on_full not in FULL_POLICIES:
            raise ValueError(f"unknown full policy: {on_full!r}")
        if late not in LATE_POLICIES:
            raise ValueError(f"unknown late policy: {late!r}")
        if cooldown_ms < 0:
            raise ValueError("cooldown_ms must be zero or positive")
        if hysteresis_ms < 0:
            raise ValueError("hysteresis_ms must be zero or positive")
        if dedupe_ms < 0:
            raise ValueError("dedupe_ms must be zero or positive")
        if max_decisions_per_window is not None and max_decisions_per_window <= 0:
            raise ValueError("max_decisions_per_window must be positive")
        if budget_window_ms <= 0:
            raise ValueError("budget_window_ms must be positive")
        if latency_samples <= 0:
            raise ValueError("latency_samples must be positive")

        self._decide = decide
        self._explicit_stream_id = bool(stream_id)
        self.stream_id = stream_id or (id_factory or (lambda: new_id("STR")))()
        self._capacity = capacity
        self._on_full = on_full
        self._late = late
        self._cooldown_ms = cooldown_ms
        self._hysteresis_ms = hysteresis_ms
        self._dedupe_ms = dedupe_ms
        self._max_decisions = max_decisions_per_window
        self._budget_window_ms = budget_window_ms
        self._latency_samples = latency_samples
        self._trace = trace
        self._recorder = recorder
        self.timeline = timeline
        self.human_attention_budget = human_attention_budget
        self._clock: Clock = clock or utcnow
        self._items: deque[Decision] = deque()
        self._wake = asyncio.Event()
        self._space = asyncio.Event()
        self._space.set()
        self._closed = False
        self._watermark: datetime | None = None
        self._last_decision: datetime | None = None
        self._last_signature: tuple[tuple[str, str | None], ...] | None = None
        self._last_signature_at: datetime | None = None
        self._window_start: datetime | None = None
        self._window_count = 0
        self._latencies: deque[float] = deque(maxlen=latency_samples)
        self._seen: OrderedDict[str, datetime] = OrderedDict()
        self._traces: dict[str, Trace] = {}
        self._trace_by_decision: dict[str, str] = {}
        self._stats = StreamStats()

    # ------------------------------------------------------------------ state
    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def pending(self) -> int:
        return len(self._items)

    @property
    def stats(self) -> StreamStats:
        return replace(self._stats)

    # ------------------------------------------------------------------ input
    def observe(
        self,
        request: DecisionRequest,
        *,
        status: str = "final",
        force: bool = False,
    ) -> list[Decision]:
        """Admit one event and return the decisions it produced.

        ``force`` skips the cooldown (use it for an owner action or a critical
        event), but not the late-event rule.
        """
        decisions = self._admit(request, status=status, force=force, revision=0, supersedes=None)
        for decision in decisions:
            self._append(decision)
        return decisions

    def revise(
        self,
        previous: Decision,
        request: DecisionRequest,
        *,
        status: str = "final",
    ) -> list[Decision]:
        """Decide again and mark the result as a revision of ``previous``."""
        decisions = self._admit(
            request,
            status=status,
            force=True,
            revision=previous.revision + 1,
            supersedes=previous.decision_id,
        )
        for decision in decisions:
            self._append(decision)
        return decisions

    def revise_with(
        self,
        previous: Decision,
        request: DecisionRequest,
        decisions: Sequence[Decision],
        *,
        status: str = "final",
    ) -> list[Decision]:
        """Push already-computed decisions as a revision of ``previous``."""
        if self._closed:
            raise RuntimeError("stream session is closed")
        if status not in DECISION_STATUSES:
            raise ValueError(f"unknown decision status: {status!r}")
        revised = [
            self._stamp(
                item,
                request,
                status=status,
                revision=previous.revision + 1,
                supersedes=previous.decision_id,
            )
            for item in decisions
        ]
        if revised:
            for item in revised:
                self._append(item)
            now = self._clock()
            self._stats.decided += len(revised)
            self._stats.revised += len(revised)
            if status == "provisional":
                self._stats.provisional += len(revised)
            self._last_decision = now
            self._last_signature = tuple((item.verb, item.action_id) for item in revised)
            self._last_signature_at = now
            self._record_decisions(revised)
        return revised

    def replay(self, requests: Iterable[DecisionRequest]) -> list[Decision]:
        """Run a sequence with event time as the clock.

        Replay does not use the async buffer; it returns every decision in
        order, so a test or an incident review can compare runs.
        """
        original = self._clock
        manual = ManualClock()
        self._clock = manual
        out: list[Decision] = []
        try:
            for request in requests:
                at = parse_iso(request.at)
                if at is not None:
                    manual.set(at)
                out.extend(
                    self._admit(
                        request,
                        status="final",
                        force=False,
                        revision=0,
                        supersedes=None,
                        record=False,
                    )
                )
        finally:
            self._clock = original
        return out

    def save(self, store: StreamCheckpointStore, key: str) -> None:
        """Persist the current snapshot through the host's store."""
        store.save(key, self.snapshot())

    def resume(self, store: StreamCheckpointStore, key: str) -> bool:
        """Load a snapshot from the host's store; return whether one existed."""
        snapshot = store.load(key)
        if snapshot is None:
            return False
        self.restore(snapshot)
        return True

    def snapshot(self) -> dict[str, object]:
        """Return the resumable state, including pending decisions and traces."""
        return {
            "stream_id": self.stream_id,
            "watermark": self._watermark.isoformat() if self._watermark else None,
            "last_decision": self._last_decision.isoformat() if self._last_decision else None,
            "last_signature": [list(item) for item in self._last_signature or ()],
            "last_signature_at": self._last_signature_at.isoformat() if self._last_signature_at else None,
            "window_start": self._window_start.isoformat() if self._window_start else None,
            "window_count": self._window_count,
            "stats": self._stats.snapshot(),
            "pending": [item.to_dict() for item in self._items],
            "traces": [trace.to_dict() for trace in self._traces.values()],
            "timeline": self.timeline.to_dict() if self.timeline is not None else None,
            "human_attention_budget": (
                self.human_attention_budget.to_dict()
                if self.human_attention_budget is not None
                else None
            ),
        }

    def restore(self, snapshot: dict[str, object]) -> None:
        """Restore watermark, cadence, counters and buffered decisions.

        A session created with an explicit ``stream_id`` refuses a checkpoint
        from another stream. A session with a generated id adopts the snapshot's
        id, which is the common resume path.
        """
        if self._closed:
            raise RuntimeError("stream session is closed")
        snapshot_id = snapshot.get("stream_id")
        if isinstance(snapshot_id, str) and snapshot_id:
            if self._explicit_stream_id and snapshot_id != self.stream_id:
                raise ValueError(
                    f"checkpoint belongs to stream {snapshot_id!r}, not {self.stream_id!r}"
                )
            self.stream_id = snapshot_id
        self._watermark = parse_iso(snapshot.get("watermark") if isinstance(snapshot.get("watermark"), str) else None)
        self._last_decision = parse_iso(
            snapshot.get("last_decision") if isinstance(snapshot.get("last_decision"), str) else None
        )
        self._last_signature = tuple(
            (str(item[0]), item[1]) for item in (snapshot.get("last_signature") or ())
        )
        self._last_signature_at = parse_iso(
            snapshot.get("last_signature_at") if isinstance(snapshot.get("last_signature_at"), str) else None
        )
        self._window_start = parse_iso(
            snapshot.get("window_start") if isinstance(snapshot.get("window_start"), str) else None
        )
        self._window_count = int(snapshot.get("window_count") or 0)
        stats = snapshot.get("stats")
        if isinstance(stats, dict):
            known = StreamStats.__dataclass_fields__
            self._stats = StreamStats(**{key: value for key, value in stats.items() if key in known})
        pending = snapshot.get("pending")
        if isinstance(pending, (list, tuple)):
            self._items = deque(
                (Decision.from_dict(item) for item in pending if isinstance(item, dict)),
                maxlen=self._capacity,
            )
            if self._items:
                self._wake.set()
                if len(self._items) < self._capacity:
                    self._space.set()
                else:
                    self._space.clear()
        traces = snapshot.get("traces")
        if isinstance(traces, (list, tuple)):
            for item in traces:
                if isinstance(item, dict):
                    trace = Trace(**item)
                    self._traces[trace.id] = trace
                    self._trace_by_decision[trace.decision_id] = trace.id
        timeline = snapshot.get("timeline")
        if isinstance(timeline, dict):
            self.timeline = DecisionTimeline.from_dict(timeline)
        budget = snapshot.get("human_attention_budget")
        if isinstance(budget, dict):
            self.human_attention_budget = HumanAttentionBudget.from_dict(budget)

    # ----------------------------------------------------------------- output
    def close(self) -> None:
        """Stop accepting events; a consumer drains what is buffered."""
        self._closed = True
        self._wake.set()
        self._space.set()

    # ---------------------------------------------------------------- private
    def _admit(
        self,
        request: DecisionRequest,
        *,
        status: str,
        force: bool,
        revision: int,
        supersedes: str | None,
        record: bool = True,
    ) -> list[Decision]:
        if self._closed:
            raise RuntimeError("stream session is closed")
        if status not in DECISION_STATUSES:
            raise ValueError(f"unknown decision status: {status!r}")

        self._stats.observed += 1
        now = self._clock()

        if self._dedupe_ms and request.event_id:
            self._purge_seen(now)
            if request.event_id in self._seen:
                self._stats.duplicates += 1
                return []
            self._seen[request.event_id] = now

        event_at = parse_iso(request.at)
        if event_at is not None:
            if self._watermark is not None and event_at < self._watermark:
                if self._late == "drop":
                    self._stats.late += 1
                    return []
            else:
                self._watermark = event_at

        if not force and self._cooldown_ms and self._last_decision is not None:
            elapsed_ms = (now - self._last_decision).total_seconds() * 1000.0
            if elapsed_ms < self._cooldown_ms:
                self._stats.throttled += 1
                return []

        if not force and not self._allow_budget(now):
            return []

        deadline_at = parse_iso(request.deadline)
        expired = deadline_at is not None and now > deadline_at
        effective_status = "provisional" if expired and status == "final" else status

        started = time.perf_counter()
        raw = self._decide(request) or ()
        self._record_latency((time.perf_counter() - started) * 1000.0)
        decisions = [
            self._stamp(item, request, status=effective_status, revision=revision, supersedes=supersedes)
            for item in raw
        ]
        if not decisions:
            return []

        signature = tuple((item.verb, item.action_id) for item in decisions)
        if not force and self._hysteresis_ms and self._last_signature is not None:
            within = (
                self._last_signature_at is not None
                and (now - self._last_signature_at).total_seconds() * 1000.0 < self._hysteresis_ms
            )
            if signature == self._last_signature and within:
                self._stats.suppressed += len(decisions)
                self._last_decision = now
                return []

        self._last_signature = signature
        self._last_signature_at = now
        self._stats.decided += len(decisions)
        if effective_status == "provisional":
            self._stats.provisional += len(decisions)
        if expired:
            self._stats.expired += len(decisions)
        if revision:
            self._stats.revised += len(decisions)
        self._last_decision = now
        if record:
            self._record_decisions(decisions)
        return decisions

    def _purge_seen(self, now: datetime) -> None:
        if not self._seen:
            return
        cutoff = now - timedelta(milliseconds=self._dedupe_ms)
        while self._seen:
            event_id, seen_at = next(iter(self._seen.items()))
            if seen_at <= cutoff or len(self._seen) > 4096:
                self._seen.popitem(last=False)
            else:
                return

    def _record_decisions(self, decisions: Sequence[Decision]) -> None:
        for decision in decisions:
            if self._trace and decision.trace_id:
                trace = Trace(id=decision.trace_id, decision_id=decision.decision_id).with_event(
                    "decided",
                    {
                        "verb": decision.verb,
                        "reason_code": decision.reason_code,
                        "stream_id": decision.stream_id,
                        "event_time": decision.event_time,
                        "revision": decision.revision,
                        "status": decision.status,
                    },
                )
                self._traces[decision.trace_id] = trace
                self._trace_by_decision[decision.decision_id] = decision.trace_id
            if self._recorder is not None:
                self._recorder(decision)
            if self.timeline is not None:
                self.timeline.add(decision)
            if self.human_attention_budget is not None:
                cost = decision.attributes.get("human_attention_cost", 0.0)
                try:
                    cost_value = float(cost)
                except (TypeError, ValueError):
                    cost_value = 0.0
                if cost_value <= 0.0 and decision.requires_approval:
                    cost_value = 0.5
                self.human_attention_budget.spend(cost_value)

    def trace(self, decision_id: str) -> Trace:
        trace_id = self._trace_by_decision.get(decision_id)
        if trace_id is None:
            raise KeyError(f"unknown decision {decision_id!r}")
        return self._traces[trace_id]

    def _allow_budget(self, now: datetime) -> bool:
        if self._max_decisions is None:
            return True
        if self._window_start is None or (now - self._window_start).total_seconds() * 1000.0 >= self._budget_window_ms:
            self._window_start = now
            self._window_count = 0
        if self._window_count >= self._max_decisions:
            self._stats.shed += 1
            return False
        self._window_count += 1
        return True

    def _record_latency(self, elapsed_ms: float) -> None:
        self._latencies.append(elapsed_ms)
        ordered = sorted(self._latencies)
        self._stats.latency_p50 = self._percentile(ordered, 50)
        self._stats.latency_p95 = self._percentile(ordered, 95)
        self._stats.latency_p99 = self._percentile(ordered, 99)

    @staticmethod
    def _percentile(ordered: Sequence[float], percent: float) -> float:
        if not ordered:
            return 0.0
        index = round((percent / 100.0) * (len(ordered) - 1))
        return round(ordered[min(len(ordered) - 1, max(0, index))], 3)

    def _stamp(
        self,
        decision: Decision,
        request: DecisionRequest,
        *,
        status: str,
        revision: int,
        supersedes: str | None,
    ) -> Decision:
        stamped = replace(
            decision,
            stream_id=self.stream_id,
            event_time=request.at,
            deadline=request.deadline or decision.deadline,
            valid_until=request.valid_until or decision.valid_until,
            supersedes=supersedes or decision.supersedes,
            revision=max(revision, decision.revision),
            status=status,
            target=request.target or decision.target,
            recipients=request.recipients or decision.recipients,
        )
        if not stamped.decision_id:
            stamped = replace(stamped, decision_id=new_id("DEC"))
        if self._trace and not stamped.trace_id:
            stamped = replace(stamped, trace_id=new_id("TRC"))
        return stamped

    def _append(self, decision: Decision) -> None:
        if self._closed:
            return
        if len(self._items) < self._capacity:
            self._items.append(decision)
            self._wake.set()
            self._space.set()
            return
        if self._on_full == "drop_newest":
            self._stats.dropped += 1
            return
        if self._on_full == "drop_oldest":
            self._items.popleft()
            self._stats.dropped += 1
        else:
            self._stats.dropped += len(self._items)
            self._items.clear()
        self._items.append(decision)
        self._wake.set()
        if len(self._items) < self._capacity:
            self._space.set()
        else:
            self._space.clear()


__all__ = [
    "Clock",
    "Decider",
    "FULL_POLICIES",
    "LATE_POLICIES",
    "ManualClock",
    "Refiner",
    "StreamSession",
    "StreamStats",
]
