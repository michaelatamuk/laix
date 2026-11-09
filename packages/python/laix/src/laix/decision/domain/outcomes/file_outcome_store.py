"""One JSON file for an outcome ledger, under a host-owned directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ledger import OutcomeLedger
from .record import Outcome


class FileOutcomeStore(OutcomeLedger):
    """An outcome ledger persisted as one JSON file.

    The store is append-oriented: ``add`` and ``record`` write the file after
    every change. The host can replace the file with its own database port.
    """

    def __init__(
        self,
        directory: str | Path,
        *,
        filename: str = "outcomes.json",
        tolerance: float = 1e-9,
    ) -> None:
        super().__init__(tolerance=tolerance)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / filename
        self.records = self._load()

    def _load(self) -> list[Outcome]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return [Outcome.from_dict(item) for item in payload.get("outcomes", [])]

    def _flush(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"outcomes": [item.to_dict() for item in self.records]},
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def add(self, outcome: Outcome) -> Outcome:
        super().add(outcome)
        self._flush()
        return outcome

    def record(self, decision_id: str, **kwargs: Any) -> Outcome:
        outcome = super().record(decision_id, **kwargs)
        self._flush()
        return outcome


__all__ = ["FileOutcomeStore"]
