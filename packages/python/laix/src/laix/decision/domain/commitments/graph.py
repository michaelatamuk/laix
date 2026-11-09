"""A graph of commitments across owners, with trust-aware dependency analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any

from ...support.time import parse_iso
from .commitment import Commitment
from .commitment_ref import CommitmentRef
from .ledger import CommitmentLedger

_NEVER = datetime.max.replace(tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class CommitmentBlocker:
    """Why one commitment is blocked by another."""

    ref: CommitmentRef
    commitment: Commitment | None
    reason: str  # missing, open, unverified or stale


@dataclass(frozen=True, slots=True)
class CommitmentGraphReport:
    """The structural problems found in one graph."""

    missing_refs: tuple[CommitmentRef, ...]
    cycles: tuple[tuple[CommitmentRef, ...], ...]
    stale_refs: tuple[CommitmentRef, ...] = ()


def _ref_for(commitment: Commitment) -> CommitmentRef:
    return CommitmentRef(
        owner=commitment.owner,
        ledger=commitment.ledger,
        id=commitment.id,
    )


def _ref_for_key(key: tuple[str, str, str]) -> CommitmentRef:
    return CommitmentRef(owner=key[0], ledger=key[1] or None, id=key[2])


def _freshness_clock(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


class CommitmentGraph:
    """A local ledger plus commitments owned by other parties.

    The graph never fetches remote state. The host resolves external
    commitments and supplies them; the graph only reasons about the result.
    """

    def __init__(
        self,
        local: CommitmentLedger | Iterable[Commitment],
        external: Iterable[Commitment] = (),
    ) -> None:
        self.local = local if isinstance(local, CommitmentLedger) else CommitmentLedger(tuple(local))
        self.external = tuple(external)
        self._items: dict[tuple[str, str, str], Commitment] = {}
        for commitment in (*self.local.all(), *self.external):
            key = commitment.key
            if key in self._items:
                raise ValueError(
                    f"duplicate commitment {commitment.id!r} for owner "
                    f"{commitment.owner!r}"
                )
            self._items[key] = commitment
        self._reverse: dict[tuple[str, str, str], list[Commitment]] | None = None
        self._critical_path: tuple[Commitment, ...] | None = None
        self._cycles: tuple[tuple[CommitmentRef, ...], ...] | None = None

    @property
    def commitments(self) -> tuple[Commitment, ...]:
        """Every commitment in the graph, sorted by owner, ledger and id."""
        return tuple(self._items[key] for key in sorted(self._items))

    def get(self, ref: CommitmentRef) -> Commitment | None:
        return self._items.get(ref.key)

    def resolve(self, ref: CommitmentRef) -> Commitment | None:
        return self.get(ref)

    @staticmethod
    def dependencies(commitment: Commitment) -> tuple[CommitmentRef, ...]:
        """Local and external references that must be done before this one."""
        local = tuple(
            CommitmentRef(
                owner=commitment.owner,
                ledger=commitment.ledger,
                id=dependency,
            )
            for dependency in commitment.depends_on
        )
        return local + commitment.external_depends_on

    def is_fresh(
        self,
        commitment: Commitment,
        now: datetime,
        max_age: timedelta,
    ) -> bool:
        """Whether a promise is still within its verification window."""
        if commitment.source != "verified":
            return True
        verified = parse_iso(commitment.verified_at)
        if verified is None:
            return False
        return now - verified <= max_age

    def stale_refs(
        self,
        now: datetime,
        max_age: timedelta,
    ) -> tuple[CommitmentRef, ...]:
        """Verified promises whose verification is older than ``max_age``."""
        found = [
            _ref_for(item)
            for item in self.commitments
            if not self.is_fresh(item, now, max_age)
        ]
        return tuple(dict.fromkeys(found))

    def blockers(
        self,
        commitment: Commitment,
        *,
        require_verified: bool = False,
        now: datetime | None = None,
        max_verification_age: timedelta | None = None,
    ) -> tuple[CommitmentBlocker, ...]:
        """Return every dependency that still blocks this commitment."""
        found: list[CommitmentBlocker] = []
        clock = _freshness_clock(now) if max_verification_age is not None else None
        for ref in self.dependencies(commitment):
            item = self.get(ref)
            if item is None:
                found.append(CommitmentBlocker(ref, None, "missing"))
            elif item.status != "done":
                found.append(CommitmentBlocker(ref, item, "open"))
            elif require_verified and not item.trusted:
                found.append(CommitmentBlocker(ref, item, "unverified"))
            elif (
                require_verified
                and max_verification_age is not None
                and clock is not None
                and not self.is_fresh(item, clock, max_verification_age)
            ):
                found.append(CommitmentBlocker(ref, item, "stale"))
        return tuple(found)

    def blocked(
        self,
        commitment: Commitment,
        *,
        require_verified: bool = False,
        now: datetime | None = None,
        max_verification_age: timedelta | None = None,
    ) -> bool:
        return bool(
            self.blockers(
                commitment,
                require_verified=require_verified,
                now=now,
                max_verification_age=max_verification_age,
            )
        )

    def blocked_open(
        self,
        *,
        require_verified: bool = False,
        now: datetime | None = None,
        max_verification_age: timedelta | None = None,
    ) -> tuple[Commitment, ...]:
        return tuple(
            item
            for item in self.local.open()
            if self.blocked(
                item,
                require_verified=require_verified,
                now=now,
                max_verification_age=max_verification_age,
            )
        )

    def next_actionable(
        self,
        now: datetime | None = None,
        *,
        require_verified: bool = False,
        max_verification_age: timedelta | None = None,
    ) -> Commitment | None:
        """Earliest open local commitment whose graph dependencies are done."""
        candidates = [
            item
            for item in self.local.open()
            if not self.blocked(
                item,
                require_verified=require_verified,
                now=now,
                max_verification_age=max_verification_age,
            )
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda item: (parse_iso(item.due) or _NEVER, -item.priority, item.id),
        )[0]

    def missing_refs(
        self,
        commitment: Commitment | None = None,
    ) -> tuple[CommitmentRef, ...]:
        """References that do not resolve anywhere in the graph."""
        source = (commitment,) if commitment is not None else self.commitments
        found: list[CommitmentRef] = []
        for item in source:
            for ref in self.dependencies(item):
                if self.get(ref) is None:
                    found.append(ref)
        return tuple(dict.fromkeys(found))

    def unverified_refs(self) -> tuple[CommitmentRef, ...]:
        """Resolved dependencies that are reported but not verified."""
        found: list[CommitmentRef] = []
        for item in self.commitments:
            for ref in self.dependencies(item):
                dependency = self.get(ref)
                if dependency is not None and not dependency.trusted:
                    found.append(ref)
        return tuple(dict.fromkeys(found))

    def validate(
        self,
        *,
        now: datetime | None = None,
        max_verification_age: timedelta | None = None,
    ) -> CommitmentGraphReport:
        """Return missing references, cycles and stale verified promises."""
        stale: tuple[CommitmentRef, ...] = ()
        if max_verification_age is not None:
            stale = self.stale_refs(
                _freshness_clock(now),
                max_verification_age,
            )
        return CommitmentGraphReport(
            missing_refs=self.missing_refs(),
            cycles=self.cycles(),
            stale_refs=stale,
        )

    def ancestors(self, ref: CommitmentRef) -> tuple[Commitment, ...]:
        """Commitments this one depends on, directly or transitively."""
        found: dict[tuple[str, str, str], Commitment] = {}
        seen = {ref.key}
        stack = [ref]
        while stack:
            current = stack.pop()
            item = self.get(current)
            if item is None:
                continue
            for dependency in self.dependencies(item):
                if dependency.key in seen:
                    continue
                child = self.get(dependency)
                if child is None:
                    continue
                seen.add(dependency.key)
                found[dependency.key] = child
                stack.append(dependency)
        return tuple(found[key] for key in sorted(found))

    def _reverse_index(self) -> dict[tuple[str, str, str], list[Commitment]]:
        if self._reverse is None:
            reverse: dict[tuple[str, str, str], list[Commitment]] = {}
            for item in self.commitments:
                for dependency in self.dependencies(item):
                    reverse.setdefault(dependency.key, []).append(item)
            self._reverse = reverse
        return self._reverse

    def descendants(self, ref: CommitmentRef) -> tuple[Commitment, ...]:
        """Commitments that depend on this one, directly or transitively."""
        reverse = self._reverse_index()
        found: dict[tuple[str, str, str], Commitment] = {}

        def walk(key: tuple[str, str, str], seen: set[tuple[str, str, str]]) -> None:
            for item in reverse.get(key, ()):
                if item.key in seen:
                    continue
                seen.add(item.key)
                found[item.key] = item
                walk(item.key, seen)

        walk(ref.key, {ref.key})
        return tuple(found[key] for key in sorted(found))

    def impact(self, ref: CommitmentRef) -> tuple[Commitment, ...]:
        """Every decision affected if this commitment changes."""
        return self.descendants(ref)

    def chain(self, ref: CommitmentRef) -> tuple[Commitment, ...]:
        """The longest dependency chain that starts at this commitment."""
        start = self.get(ref)
        if start is None:
            return ()

        def walk(item: Commitment, seen: set[tuple[str, str, str]]) -> tuple[Commitment, ...]:
            best: tuple[Commitment, ...] = (item,)
            for dependency in self.dependencies(item):
                if dependency.key in seen:
                    continue
                child = self.get(dependency)
                if child is None:
                    continue
                candidate = (item,) + walk(child, seen | {dependency.key})
                if len(candidate) > len(best):
                    best = candidate
            return best

        return walk(start, {ref.key})

    def critical_path(self) -> tuple[Commitment, ...]:
        """Longest dependency chain in the whole graph."""
        if self._critical_path is None:
            best: tuple[Commitment, ...] = ()
            for item in self.commitments:
                path = self.chain(_ref_for(item))
                if len(path) > len(best):
                    best = path
            self._critical_path = best
        return self._critical_path

    def cycles(self) -> tuple[tuple[CommitmentRef, ...], ...]:
        """Dependency cycles, each returned as its ordered references."""
        if self._cycles is not None:
            return self._cycles
        found: list[tuple[CommitmentRef, ...]] = []
        seen: set[tuple[tuple[str, str, str], ...]] = set()
        complete: set[tuple[str, str, str]] = set()

        def walk(key: tuple[str, str, str], stack: list[tuple[str, str, str]]) -> None:
            if key in stack:
                start = stack.index(key)
                cycle = stack[start:] + [key]
                canonical = tuple(sorted(set(cycle)))
                if canonical not in seen:
                    seen.add(canonical)
                    found.append(tuple(_ref_for_key(item) for item in cycle))
                return
            if key in complete:
                return
            item = self._items.get(key)
            if item is None:
                return
            stack.append(key)
            for dependency in self.dependencies(item):
                walk(dependency.key, stack)
            stack.pop()
            complete.add(key)

        for key in self._items:
            walk(key, [])
        self._cycles = tuple(found)
        return self._cycles

    def subgraph(self, refs: Iterable[CommitmentRef]) -> CommitmentGraph:
        """The induced subgraph for the supplied references."""
        keys = {ref.key for ref in refs}
        local = CommitmentLedger(
            tuple(item for item in self.local.all() if item.key in keys)
        )
        external = tuple(item for item in self.external if item.key in keys)
        return CommitmentGraph(local, external)

    def neighborhood(self, ref: CommitmentRef) -> CommitmentGraph:
        """The commitment, its ancestors and its descendants."""
        found: dict[tuple[str, str, str], Commitment] = {}
        target = self.get(ref)
        if target is not None:
            found[target.key] = target
        for item in (*self.ancestors(ref), *self.descendants(ref)):
            found[item.key] = item
        return self.subgraph(_ref_for(item) for item in found.values())

    def redacted(self, *, keep_subject: bool = False) -> CommitmentGraph:
        """A copy with every payload removed and, by default, every subject hidden."""

        def clean(item: Commitment) -> Commitment:
            return replace(
                item,
                subject=item.subject if keep_subject else "",
                payload={},
            )

        return CommitmentGraph(
            CommitmentLedger(tuple(clean(item) for item in self.local.all())),
            tuple(clean(item) for item in self.external),
        )

    def to_mermaid(self) -> str:
        """Render the graph as a Mermaid flowchart."""
        ids = {item.key: f"n{index}" for index, item in enumerate(self.commitments)}
        lines = ["flowchart LR"]
        for item in self.commitments:
            label = (
                f"{item.owner} · {item.id} · {item.subject} · {item.status}"
                .replace('"', "'")
                .replace("\n", " ")
            )
            lines.append(f'    {ids[item.key]}["{label}"]')
        for item in self.commitments:
            for dependency in self.dependencies(item):
                child = self.get(dependency)
                if child is None:
                    continue
                kind = (
                    "depends_on"
                    if dependency in _local_refs(item)
                    else "external_depends_on"
                )
                lines.append(f"    {ids[item.key]} -->|{kind}| {ids[child.key]}")
        return "\n".join(lines)

    def to_dot(self) -> str:
        """Render the graph as a Graphviz digraph."""
        ids = {item.key: f"n{index}" for index, item in enumerate(self.commitments)}
        lines = ["digraph commitments {"]
        for item in self.commitments:
            label = (
                f"{item.owner} · {item.id} · {item.subject} · {item.status}"
                .replace('"', '\\"')
                .replace("\n", " ")
            )
            lines.append(f'  {ids[item.key]} [label="{label}"];')
        for item in self.commitments:
            for dependency in self.dependencies(item):
                child = self.get(dependency)
                if child is None:
                    continue
                kind = (
                    "depends_on"
                    if dependency in _local_refs(item)
                    else "external_depends_on"
                )
                lines.append(
                    f'  {ids[item.key]} -> {ids[child.key]} [label="{kind}"];'
                )
        lines.append("}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, object]:
        return {
            "local": self.local.to_dict(),
            "external": [item.to_dict() for item in self.external],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CommitmentGraph":
        """Rebuild a graph from a ``to_dict`` payload."""
        local_payload = payload.get("local") or {}
        external_payload = payload.get("external") or ()
        local = CommitmentLedger.from_dict(dict(local_payload))
        return cls(
            local,
            tuple(Commitment.from_dict(dict(item)) for item in external_payload),
        )


def _local_refs(commitment: Commitment) -> tuple[CommitmentRef, ...]:
    return tuple(
        CommitmentRef(
            owner=commitment.owner,
            ledger=commitment.ledger,
            id=dependency,
        )
        for dependency in commitment.depends_on
    )


__all__ = ["CommitmentBlocker", "CommitmentGraph", "CommitmentGraphReport"]
