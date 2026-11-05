"""Save, load and delete one stream snapshot."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StreamCheckpointStore(Protocol):
    """Save, load and delete one stream snapshot."""

    def save(self, key: str, snapshot: dict[str, Any]) -> None:
        ...

    def load(self, key: str) -> dict[str, Any] | None:
        ...

    def delete(self, key: str) -> None:
        ...


__all__ = ["StreamCheckpointStore"]
