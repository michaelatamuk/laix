"""The request the action policy consumes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...decisions import ActionOption, Situation


@dataclass(frozen=True)
class ActionPolicyRequest:
    situation: Situation
    options: tuple[ActionOption, ...]
    attributes: dict[str, Any] = field(default_factory=dict)


__all__ = ["ActionPolicyRequest"]
