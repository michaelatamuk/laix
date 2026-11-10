"""A utility planner with an explicit downside bound."""

from __future__ import annotations

from typing import Any

from ....contract.planner_policy import PlannerInput, PlannerResult
from ....support.values import clamp
from ..utility.utility_planner import UtilityModel, UtilityPlanner


def _risk(option: Any, key: str, fallback: float) -> float:
    params = getattr(option, "params", {}) or {}
    payload = params.get("risk_bound", params.get("risk", {}))
    if not isinstance(payload, dict):
        payload = {}
    value = payload.get(key, params.get(key, fallback))
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


class RiskBoundedPlanner:
    """Choose the best option whose downside stays inside a hard limit."""

    name = "risk_bounded.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        *,
        max_loss: float = 0.5,
        penalty: float = 0.0,
    ) -> None:
        if max_loss < 0:
            raise ValueError("max_loss must not be negative")
        if penalty < 0:
            raise ValueError("penalty must not be negative")
        self.model = model or UtilityModel()
        self.max_loss = max_loss
        self.penalty = penalty
        self._utility = UtilityPlanner(self.model)

    def solve(self, problem: PlannerInput) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        rows: list[dict[str, Any]] = []
        for option in options:
            utility = model.score(option)
            worst = _risk(option, "worst_case_loss", option.risk)
            cvar = _risk(option, "cvar_loss", worst)
            feasible = model.feasible(option) and cvar <= self.max_loss
            total = round(utility - self.penalty * clamp(cvar), 6)
            rows.append(
                {
                    "option": option,
                    "utility": round(utility, 6),
                    "worst_case_loss": round(worst, 6),
                    "cvar_loss": round(cvar, 6),
                    "total": total,
                    "feasible": feasible,
                }
            )

        feasible = [row for row in rows if row["feasible"]]
        if not feasible:
            return self._wait(
                "no_feasible_option",
                "every option exceeds the downside limit",
                attributes={"risk_limit": self.max_loss},
            )

        feasible.sort(key=lambda row: (-row["total"], row["option"].id))
        best = feasible[0]
        second = feasible[1]["total"] if len(feasible) > 1 else None
        alternatives = tuple(
            {
                "action_id": row["option"].id,
                "verb": row["option"].verb,
                "name": row["option"].name,
                "utility": row["utility"],
                "total": row["total"],
                "cvar_loss": row["cvar_loss"],
                "rejected_reason_code": (
                    "risk_limit" if not row["feasible"] else "lower_risk_adjusted_score"
                ),
            }
            for row in rows
            if row["option"].id != best["option"].id
        )
        return PlannerResult(
            verb=best["option"].verb,
            confidence=self._confidence(best["total"], second),
            reason_code="risk_bounded",
            rationale=(
                f"{best['option'].id} keeps CVaR {best['cvar_loss']:.3f} within "
                f"{self.max_loss:.3f}"
            ),
            action_id=best["option"].id,
            requires_approval=bool(best["option"].requires_approval),
            reversible=best["option"].reversible,
            score=best["total"],
            alternatives=alternatives,
            attributes={
                "risk_limit": self.max_loss,
                "worst_case_loss": best["worst_case_loss"],
                "cvar_loss": best["cvar_loss"],
                "utility": best["utility"],
            },
        )

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))

    @staticmethod
    def _wait(
        reason_code: str,
        rationale: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> PlannerResult:
        return PlannerResult(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
            attributes=dict(attributes or {}),
        )


__all__ = ["RiskBoundedPlanner"]
