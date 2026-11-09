"""The utility and attention parts of one option's score."""

from __future__ import annotations

from dataclasses import dataclass

from .human_attention_effect import HumanAttentionEffect


@dataclass(frozen=True, slots=True)
class HumanAttentionScore:
    """The utility and attention parts of one option's score."""

    utility: float
    human_attention: float
    total: float
    effect: HumanAttentionEffect
    remaining: float
    blocked: str | None = None


__all__ = ["HumanAttentionScore"]
