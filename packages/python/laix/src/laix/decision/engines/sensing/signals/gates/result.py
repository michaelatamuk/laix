"""What a fired gate decides."""

from __future__ import annotations

from typing import NamedTuple

from .....support.verbs import Verb
from .reason import ReasonCode


class GateResult(NamedTuple):
    """The verb, reason and two delivery flags chosen by one gate."""

    verb: Verb
    reason_code: ReasonCode | str
    record: bool
    deliver: bool


__all__ = ["GateResult"]
