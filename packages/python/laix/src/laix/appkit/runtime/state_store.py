"""Storage-free state store contracts.

The app owns the database. LAIX defines the save, load and delete interface so
an experience snapshot can outlive one request without LAIX becoming a memory
product.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .state import ExperienceState


@runtime_checkable
class StateStore(Protocol):
    def save(self, key: str, state: ExperienceState) -> None:
        ...

    def load(self, key: str) -> ExperienceState | None:
        ...

    def delete(self, key: str) -> None:
        ...


__all__ = ["StateStore"]
