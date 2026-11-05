"""How the host can undo an attention decision."""

from __future__ import annotations

from ....support.verbs import Verb


def undo_hint(verb: str, reversible: bool) -> str | None:
    """Return the affordance a UI can offer, or None."""
    if verb in {Verb.GUIDE, Verb.ASK}:
        return "withdraw"
    if verb == Verb.ACT:
        return "cancel" if reversible else None
    return None


__all__ = ["undo_hint"]
