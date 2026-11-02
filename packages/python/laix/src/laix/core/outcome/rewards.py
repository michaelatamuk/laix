"""Map a measured outcome label to a reward in ``0..1``."""

from __future__ import annotations


def reward_for_label(label: str) -> float | None:
    """Map a measured outcome label to a reward in ``0..1``.

    ``unknown`` returns ``None``: the learner skips it rather than inventing a
    reward.
    """
    key = (label or "").strip().lower()
    return {"helped": 1.0, "neutral": 0.5, "hurt": 0.0}.get(key)


__all__ = ["reward_for_label"]
