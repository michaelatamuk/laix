"""The seven verbs are the whole north interface."""

from __future__ import annotations

from enum import StrEnum


class Verb(StrEnum):
    """One decidable word. The values are the JSON contract."""

    WAIT = "wait"
    OBSERVE = "observe"
    GUIDE = "guide"
    ASK = "ask"
    ACT = "act"
    VERIFY = "verify"
    ESCALATE = "escalate"


#: An app receives one of these decisions, with approval carried as a flag
#: rather than as its own verb.
VERBS: tuple[str, ...] = tuple(verb.value for verb in Verb)

__all__ = ["VERBS", "Verb"]
