"""Types shared by the execution bridge and its async mixin."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from ...decision.domain.decisions import ActionOption

Handler = Callable[[ActionOption, dict[str, Any]], dict[str, Any]]
AsyncHandler = Callable[[ActionOption, dict[str, Any]], Awaitable[dict[str, Any]]]

__all__ = ["AsyncHandler", "Handler"]
