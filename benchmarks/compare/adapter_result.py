"""Result of one external-adapter run."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """One external adapter's capability or operational result."""

    name: str
    available: bool
    decisions: int = 0
    interrupts: int = 0
    mean_latency_ms: float = 0.0
    dependencies: tuple[str, ...] = ()
    glue_lines: int = 0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "available": self.available,
            "decisions": self.decisions,
            "interrupts": self.interrupts,
            "mean_latency_ms": round(self.mean_latency_ms, 6),
            "dependencies": list(self.dependencies),
            "glue_lines": self.glue_lines,
            "notes": list(self.notes),
        }


__all__ = ["AdapterResult"]
