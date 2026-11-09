"""One JSON file per experience state, under a host-owned directory."""

from __future__ import annotations

import json
from pathlib import Path

from .state import ExperienceState


class FileStateStore:
    """One JSON file per experience state, under a host-owned directory.

    The format is ``ExperienceState.snapshot()``. It is deliberately plain JSON:
    the host can inspect, back up or migrate the file without importing LAIX.
    """

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "".join(
            "_" if character in '/\\:*?"<>|' else character
            for character in key
        )
        return self.directory / f"{safe}.json"

    def save(self, key: str, state: ExperienceState) -> None:
        path = self._path(key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(state.snapshot(), indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def load(self, key: str) -> ExperienceState | None:
        path = self._path(key)
        if not path.exists():
            return None
        return ExperienceState.from_snapshot(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


__all__ = ["FileStateStore"]
