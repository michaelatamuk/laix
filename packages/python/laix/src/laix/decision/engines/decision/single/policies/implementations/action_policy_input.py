"""Input for one action-policy decision."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ......domain.decisions import ActionOption, Situation


@dataclass(frozen=True)
class ActionPolicyInput:
    situation: Situation
    options: tuple[ActionOption, ...]
    attributes: dict[str, Any] = field(default_factory=dict)


__all__ = ["ActionPolicyInput"]
