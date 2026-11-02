"""One parity fixture: a request and the decisions it should produce."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    request: Any
    expected: tuple[Mapping[str, Any], ...] = ()


__all__ = ["Case"]
