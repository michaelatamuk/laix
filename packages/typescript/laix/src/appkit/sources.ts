export async function* fromQueue<T>(queue: AsyncIterable<T | null>): AsyncIterable<T> {
  for await (const item of queue) {
    if (item === null) return;
    yield item;
  }
}

export async function* fromSync<T>(items: Iterable<T>): AsyncIterable<T> {
  for (const item of items) yield item;
}
