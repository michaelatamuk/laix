"""Counterfactual search for rule-based and planner decisions (CDA search).

The linear ``counterfactual_attribution`` assumes component scores. This module
searches a caller-supplied decision function over bounded numeric inputs. It
returns the smallest weighted L1 change, up to a configurable number of changed
variables and a bounded evaluation budget.

The search is deterministic and exact over the generated grid when the budget
is not reached. It is a research prototype, not a global optimizer.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations, product


@dataclass(frozen=True, slots=True)
class CounterfactualVariable:
    """One bounded input to the decision function."""

    name: str
    value: float
    lower: float
    upper: float
    step: float = 0.1
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class CounterfactualChange:
    """One changed variable."""

    name: str
    old: float
    new: float
    delta: float


@dataclass(frozen=True, slots=True)
class CounterfactualSearchResult:
    """The chosen action and the smallest searched counterfactual."""

    chosen_id: str
    counterfactual_id: str | None
    changes: tuple[CounterfactualChange, ...]
    distance: float
    evaluations: int


def _grid(variable: CounterfactualVariable) -> tuple[float, ...]:
    if variable.step <= 0:
        raise ValueError("step must be positive")
    if variable.lower > variable.upper:
        raise ValueError("lower must not exceed upper")
    if not variable.lower <= variable.value <= variable.upper:
        raise ValueError("value must be inside [lower, upper]")
    count = int(round((variable.upper - variable.lower) / variable.step))
    values = {
        round(variable.lower + index * variable.step, 9)
        for index in range(count + 1)
    }
    values.add(round(variable.value, 9))
    return tuple(sorted(values))


def _candidate(
    variables: Sequence[CounterfactualVariable],
    names: tuple[str, ...],
    values: tuple[float, ...],
    base: Mapping[str, float],
) -> tuple[float, dict[str, float]] | None:
    changes = {
        name: value
        for name, value in zip(names, values)
        if abs(value - base[name]) > 1e-12
    }
    if not changes:
        return None
    distance = sum(
        variable.weight * abs(changes.get(variable.name, variable.value) - variable.value)
        for variable in variables
    )
    return distance, changes


def counterfactual_search(
    decide: Callable[[Mapping[str, float]], str],
    variables: Sequence[CounterfactualVariable],
    *,
    max_changes: int = 2,
    max_evaluations: int = 20000,
) -> CounterfactualSearchResult:
    """Find the smallest weighted L1 change that flips the decision."""
    if max_changes < 1:
        raise ValueError("max_changes must be at least one")
    if max_evaluations < 1:
        raise ValueError("max_evaluations must be at least one")
    base = {variable.name: variable.value for variable in variables}
    chosen = str(decide(base))
    grids = {variable.name: _grid(variable) for variable in variables}
    candidates: list[tuple[float, tuple[str, ...], tuple[float, ...]]] = []
    for size in range(1, min(max_changes, len(variables)) + 1):
        for group in combinations(variables, size):
            names = tuple(variable.name for variable in group)
            for values in product(*(grids[name] for name in names)):
                candidate = _candidate(variables, names, values, base)
                if candidate is None:
                    continue
                distance, _ = candidate
                candidates.append((round(distance, 9), names, values))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    evaluations = 0
    for distance, names, values in candidates:
        if evaluations >= max_evaluations:
            break
        probe = dict(base)
        for name, value in zip(names, values):
            probe[name] = value
        result = str(decide(probe))
        evaluations += 1
        if result == chosen:
            continue
        changes = tuple(
            CounterfactualChange(
                name=name,
                old=round(base[name], 9),
                new=round(value, 9),
                delta=round(value - base[name], 9),
            )
            for name, value in zip(names, values)
            if abs(value - base[name]) > 1e-12
        )
        return CounterfactualSearchResult(
            chosen_id=chosen,
            counterfactual_id=result,
            changes=changes,
            distance=round(distance, 9),
            evaluations=evaluations,
        )
    return CounterfactualSearchResult(
        chosen_id=chosen,
        counterfactual_id=None,
        changes=(),
        distance=0.0,
        evaluations=evaluations,
    )


__all__ = [
    "CounterfactualChange",
    "CounterfactualSearchResult",
    "CounterfactualVariable",
    "counterfactual_search",
]
