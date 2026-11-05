"""The utility and attention parts of one option's score."""

from __future__ import annotations

from dataclasses import dataclass

from .attention_effect import AttentionEffect


@dataclass(frozen=True, slots=True)
class AttentionScore:
    """The utility and attention parts of one option's score."""

    utility: float
    attention: float
    total: float
    effect: AttentionEffect
    remaining: float
    blocked: str | None = None


__all__ = ["AttentionScore"]
