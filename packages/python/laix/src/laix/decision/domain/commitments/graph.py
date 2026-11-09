"""A graph of commitments across owners, with trust-aware dependency analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

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
    reason: str  # missing, open or unverified


def _ref_for(commitment: Commitment) -> CommitmentRef:
    return CommitmentRef(
        owner=commitment.owner,
        ledger=commitment.ledger,
        id=commitment.id,
    )


def _ref_for_key(key: tuple[str, str, str]) -> CommitmentRef:
    return CommitmentRef(owner=key[0], ledger=key[1] or None, id=key[2])


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

    def blockers(
        self,
        commitment: Commitment,
        *,
        require_verified: bool = False,
    ) -> tuple[CommitmentBlocker, ...]:
        """Return every dependency that still blocks this commitment."""
        found: list[CommitmentBlocker] = []
        for ref in self.dependencies(commitment):
            item = self.get(ref)
            if item is None:
                found.append(CommitmentBlocker(ref, None, "missing"))
            elif item.status != "done":
                found.append(CommitmentBlocker(ref, item, "open"))
            elif require_verified and not item.trusted:
                found.append(CommitmentBlocker(ref, item, "unverified"))
        return tuple(found)

    def blocked(
        self,
        commitment: Commitment,
        *,
        require_verified: bool = False,
    ) -> bool:
        return bool(self.blockers(commitment, require_verified=require_verified))

    def blocked_open(
        self,
        *,
        require_verified: bool = False,
    ) -> tuple[Commitment, ...]:
        return tuple(
            item
            for item in self.local.open()
            if self.blocked(item, require_verified=require_verified)
        )

    def next_actionable(
        self,
        now: datetime | None = None,
        *,
        require_verified: bool = False,
    ) -> Commitment | None:
        """Earliest open local commitment whose graph dependencies are done."""
        candidates = [
            item
            for item in self.local.open()
            if not self.blocked(item, require_verified=require_verified)
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

    def descendants(self, ref: CommitmentRef) -> tuple[Commitment, ...]:
        """Commitments that depend on this one, directly or transitively."""
        reverse: dict[tuple[str, str, str], list[Commitment]] = {}
        for item in self.commitments:
            for dependency in self.dependencies(item):
                reverse.setdefault(dependency.key, []).append(item)
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
        best: tuple[Commitment, ...] = ()
        for item in self.commitments:
            path = self.chain(_ref_for(item))
            if len(path) > len(best):
                best = path
        return best

    def cycles(self) -> tuple[tuple[CommitmentRef, ...], ...]:
        """Dependency cycles, each returned as its ordered references."""
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
        return tuple(found)

    def to_dict(self) -> dict[str, object]:
        return {
            "local": self.local.to_dict(),
            "external": [item.to_dict() for item in self.external],
        }


__all__ = ["CommitmentBlocker", "CommitmentGraph"]
