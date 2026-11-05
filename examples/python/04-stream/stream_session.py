"""One event becomes a decision in a stream session."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from laix import Context, DecisionRequest, Layer, Signal


async def main() -> None:
    layer = Layer()
    stream = layer.stream(stream_id="STR-DEMO", capacity=4, cooldown_ms=500)

    stream.observe(
        DecisionRequest(
            subject="a bill is due",
            at="2026-11-01T10:00:00+00:00",
            signals=(Signal(id="s-1", kind="bill", severity="high", confidence=0.9),),
            context=Context(now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc), quiet_hours=None),
        )
    )
    stream.close()

    async for decision in stream.decisions():
        print(decision.verb, decision.reason_code, decision.stream_id, decision.status)


if __name__ == "__main__":
    asyncio.run(main())
