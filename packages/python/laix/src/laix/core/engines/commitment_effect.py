"""What one option does to the open commitments."""

from __future__ import annotations

from dataclasses import dataclass

from .commitment_ids import _ids


@dataclass(frozen=True, slots=True)
class CommitmentEffect:
    """What one option does to the open commitments."""

    fulfills: tuple[str, ...] = ()
    violates: tuple[str, ...] = ()
    creates: tuple[str, ...] = ()
    hard: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fulfills", _ids(self.fulfills))
        object.__setattr__(self, "violates", _ids(self.violates))
        object.__setattr__(self, "creates", _ids(self.creates))


__all__ = ["CommitmentEffect"]
