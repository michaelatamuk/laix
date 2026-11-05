"""Keep malformed source frames in a dead-letter queue."""

from __future__ import annotations

import asyncio

from laix import DeadLetterQueue, from_ndjson


async def lines():
    yield '{"subject":"a","at":"2026-11-01T10:00:00+00:00"}\n'
    yield '{"subject":\n'
    yield '{"subject":"b","at":"2026-11-01T10:00:01+00:00"}\n'


dead = DeadLetterQueue()


async def main() -> list[str]:
    return [
        item.subject
        async for item in from_ndjson(lines(), on_error=dead, strict=False)
    ]


print(" ".join(asyncio.run(main())), len(dead), "JSONDecodeError" in dead.all()[0].error)
