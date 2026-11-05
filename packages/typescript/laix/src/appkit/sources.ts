import type { DecisionRequest } from "../core/contracts.ts";

export async function* fromQueue<T>(queue: AsyncIterable<T | null>): AsyncIterable<T> {
  for await (const item of queue) {
    if (item === null) return;
    yield item;
  }
}

export async function* fromSync<T>(items: Iterable<T>): AsyncIterable<T> {
  for (const item of items) yield item;
}

export async function* fromNdjson(
  lines: AsyncIterable<string> | Iterable<string>,
): AsyncIterable<DecisionRequest> {
  for await (const line of lines) {
    const text = line.trim();
    if (text) yield JSON.parse(text) as DecisionRequest;
  }
}

export async function* fromSse(
  lines: AsyncIterable<string> | Iterable<string>,
): AsyncIterable<DecisionRequest> {
  let data: string[] = [];
  for await (const line of lines) {
    if (line.startsWith("data:")) {
      data.push(line.slice(5).trim());
    } else if (!line.trim() && data.length) {
      yield JSON.parse(data.join("\n")) as DecisionRequest;
      data = [];
    }
  }
  if (data.length) yield JSON.parse(data.join("\n")) as DecisionRequest;
}
