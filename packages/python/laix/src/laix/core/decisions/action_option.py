"""A candidate action the app can afford to offer LAIX."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..serialize import to_primitive, to_string_tuple
from ..values import clamp
from ..verbs import VERBS
from ..version import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ActionOption:
    """A candidate action the app can afford to offer LAIX.

    The app describes cost, risk and benefit in its own units; LAIX only needs
    comparable numbers and the verb.  Execution is delegated back to the app
    through a named skill, never performed by this package.
    """

    id: str
    verb: str
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    expected_benefit: float = 0.5
    cost: float = 0.0
    risk: float = 0.0
    latency_ms: int = 0
    interrupt_cost: float = 0.0
    destructive: bool = False
    reversible: bool = True
    requires_approval: bool = False
    addresses: tuple[str, ...] = ()
    rationale: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.verb not in VERBS:
            raise ValueError(f"unknown verb: {self.verb}")
        object.__setattr__(self, "expected_benefit", clamp(self.expected_benefit))
        object.__setattr__(self, "risk", clamp(self.risk))
        object.__setattr__(self, "interrupt_cost", clamp(self.interrupt_cost))
        object.__setattr__(self, "addresses", to_string_tuple(self.addresses))
        if self.destructive:
            object.__setattr__(self, "requires_approval", True)

    @property
    def utility(self) -> float:
        """Deterministic utility used only to break ties inside one verb band."""
        return round(self.expected_benefit - 0.25 * self.risk - 0.15 * self.interrupt_cost, 6)

    def to_dict(self) -> dict:
        payload = to_primitive(self)
        payload["utility"] = self.utility
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "ActionOption":
        data = dict(payload)
        data.pop("utility", None)
        if "addresses" in data:
            data["addresses"] = to_string_tuple(data["addresses"])
        return cls(**data)


__all__ = ["ActionOption"]
