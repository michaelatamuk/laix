"""Read a stream from NDJSON lines."""

from __future__ import annotations

import asyncio

from laix import from_ndjson


async def lines():
    yield '{"subject":"a","at":"2026-11-01T10:00:00+00:00"}\n'
    yield '{"subject":"b","at":"2026-11-01T10:00:01+00:00"}\n'


async def main() -> list[str]:
    return [item.subject async for item in from_ndjson(lines())]


print(" ".join(asyncio.run(main())))
