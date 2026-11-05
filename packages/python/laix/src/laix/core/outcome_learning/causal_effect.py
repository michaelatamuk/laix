"""The estimated effect of one arm against another."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CausalEffect:
    """The estimated effect of one arm against another."""

    treatment: str
    control: str
    estimate: float
    treated: int
    control_size: int
    method: str
    standard_error: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None


__all__ = ["CausalEffect"]
