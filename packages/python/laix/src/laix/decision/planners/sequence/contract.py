"""The shared contract for finite-horizon decision sequences.

A sequence planner chooses one option at each step of a known horizon. It is
different from ``Planner``, which answers one live decision at a time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ...domain.commitments import Commitment
from ...domain.decisions import ActionOption
from ..single.human_attention.human_attention_budget import HumanAttentionBudget


@dataclass(frozen=True, slots=True)
class DecisionStep:
    """The options available at one moment in the sequence."""

    at: str
    options: tuple[ActionOption, ...]


@dataclass(frozen=True, slots=True)
class DecisionScenario:
    """A finite deterministic decision sequence."""

    steps: tuple[DecisionStep, ...]
    commitments: tuple[Commitment, ...] = ()
    human_attention_budget: HumanAttentionBudget | None = None
    open_penalty: float = 0.5


@dataclass(frozen=True, slots=True)
class DecisionPlan:
    """The chosen option at each step and the search evidence."""

    actions: tuple[str, ...]
    score: float
    attention_spent: float
    violations: tuple[str, ...]
    nodes: int
    optimal: bool


@runtime_checkable
class SequencePlanner(Protocol):
    """A planner that chooses a chain of actions, not one live decision."""

    name: str

    def plan(self, scenario: DecisionScenario) -> DecisionPlan:
        """Return one action per step in ``scenario``."""


__all__ = [
    "DecisionPlan",
    "DecisionScenario",
    "DecisionStep",
    "SequencePlanner",
]
