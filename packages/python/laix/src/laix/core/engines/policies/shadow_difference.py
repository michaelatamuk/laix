"""Where the shadow policy disagreed with the primary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...decisions import Decision


@dataclass(frozen=True, slots=True)
class ShadowDifference:
    """Where the shadow policy disagreed with the primary."""

    request: Any
    primary: tuple[Decision, ...]
    shadow: tuple[Decision, ...]


__all__ = ["ShadowDifference"]
