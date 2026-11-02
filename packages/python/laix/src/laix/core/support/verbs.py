"""The seven verbs are the whole north interface."""

from __future__ import annotations

# An app receives one of these decisions, with approval carried as a flag
# rather than as its own verb.
VERBS: tuple[str, ...] = ("wait", "observe", "guide", "ask", "act", "verify", "escalate")

__all__ = ["VERBS"]
