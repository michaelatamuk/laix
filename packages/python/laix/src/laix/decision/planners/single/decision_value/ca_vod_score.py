"""The score terms for one CA-VOD option."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CAVODScore:
    """The four live terms plus the information, option and future values."""

    utility: float
    commitment: float
    execution: float
    human_attention: float
    information: float
    option: float
    future: float
    total: float


__all__ = ["CAVODScore"]
