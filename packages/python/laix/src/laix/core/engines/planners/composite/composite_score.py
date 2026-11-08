"""The utility, commitment, execution and attention parts of one live plan."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompositeScore:
    """The utility, commitment, execution and attention parts of one option."""

    utility: float
    commitment: float
    execution: float
    human_attention: float
    total: float


__all__ = ["CompositeScore"]
