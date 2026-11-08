"""Counterfactual decision attribution (CDA).

For a linear additive decision, this module answers: what is the smallest
single-component change that would make an alternative overtake the chosen
option?

The result is a ranked set of sufficient counterfactuals. It is exact for the
composite score because the score is additive. A rule-based or planning-based
decision would need the search version described in the research memo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ....decisions import Decision


_COMPONENT_KEYS = {
    "utility": "utility",
    "commitment": "commitment_score",
    "execution": "execution_score",
    "human_attention": "human_attention_score",
}

_ALTERNATIVE_KEYS = {
    "utility": "utility",
    "commitment": "commitment",
    "execution": "execution",
    "human_attention": "human_attention",
}


@dataclass(frozen=True, slots=True)
class Counterfactual:
    """One sufficient single-component change."""

    alternative_id: str
    component: str
    delta: float
    chosen_total: float
    alternative_total: float
    resulting_total: float
    explanation: str


@dataclass(frozen=True, slots=True)
class CounterfactualReport:
    """Ranked counterfactuals for one decision."""

    chosen_id: str
    chosen_total: float
    counterfactuals: tuple[Counterfactual, ...]
    minimal: Counterfactual | None


def counterfactual_attribution(
    decision: Decision,
    *,
    components: Iterable[str] | None = None,
    margin: float = 1e-6,
) -> CounterfactualReport:
    """Return the smallest single-component changes that flip the decision.

    ``decision.attributes`` must carry the component scores, and each
    alternative must carry the matching component keys. This is true for
    decisions produced by the live composite and value-of-decision planners.
    """
    chosen_id = decision.action_id or "chosen"
    chosen_total = float(decision.score or 0.0)
    attributes = decision.attributes or {}
    requested = tuple(components or _COMPONENT_KEYS)
    available = tuple(
        component
        for component in requested
        if component in _COMPONENT_KEYS
        and _COMPONENT_KEYS[component] in attributes
    )
    if not available or not decision.alternatives:
        return CounterfactualReport(
            chosen_id=chosen_id,
            chosen_total=chosen_total,
            counterfactuals=(),
            minimal=None,
        )

    rows: list[Counterfactual] = []
    for alternative in decision.alternatives:
        alternative_id = str(
            alternative.get("action_id") or alternative.get("actionId") or ""
        )
        alternative_total = float(alternative.get("total", 0.0))
        gap = chosen_total - alternative_total
        if gap <= 0:
            continue
        for component in available:
            alternative_key = _ALTERNATIVE_KEYS[component]
            if alternative.get(alternative_key) is None:
                continue
            delta = max(0.0, gap + margin)
            rows.append(
                Counterfactual(
                    alternative_id=alternative_id,
                    component=component,
                    delta=round(delta, 6),
                    chosen_total=round(chosen_total, 6),
                    alternative_total=round(alternative_total, 6),
                    resulting_total=round(alternative_total + delta, 6),
                    explanation=(
                        f"{alternative_id} overtakes {chosen_id} if "
                        f"{component} increases by {delta:.6f}"
                    ),
                )
            )

    rows.sort(key=lambda row: (row.delta, row.alternative_id, row.component))
    return CounterfactualReport(
        chosen_id=chosen_id,
        chosen_total=round(chosen_total, 6),
        counterfactuals=tuple(rows),
        minimal=rows[0] if rows else None,
    )


__all__ = [
    "Counterfactual",
    "CounterfactualReport",
    "counterfactual_attribution",
]
