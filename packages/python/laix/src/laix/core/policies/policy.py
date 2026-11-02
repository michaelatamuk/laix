"""The smallest contract a policy plugin implements."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Policy(Protocol):
    """The smallest contract a policy plugin implements."""

    name: str

    def decide(self, request: Any) -> list[Any]:
        ...


__all__ = ["Policy"]
