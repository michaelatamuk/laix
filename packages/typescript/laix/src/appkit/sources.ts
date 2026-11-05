import type { DecisionRequest } from "../core/contracts.ts";

export interface DeadLetter {
  raw: string;
  error: string;
  at: string;
}

export class DeadLetterQueue {
  readonly limit: number;
  private items: DeadLetter[] = [];

  constructor(limit = 100) {
    if (limit <= 0) throw new Error("limit must be positive");
    this.limit = limit;
  }

  add(raw: string, error: unknown): void {
    const message = error instanceof Error ? `${error.name}: ${error.message}` : String(error);
    this.items.push({ raw, error: message, at: new Date().toISOString() });
    if (this.items.length > this.limit) {
      this.items.splice(0, this.items.length - this.limit);
    }
  }

  errorHandler(): (raw: string, error: unknown) => void {
    return (raw, error) => this.add(raw, error);
  }

  all(): DeadLetter[] {
    return [...this.items];
  }

  clear(): void {
    this.items = [];
  }

  get length(): number {
    return this.items.length;
  }
}

export interface SourceOptions {
  onError?: (raw: string, error: unknown) => void;
  strict?: boolean;
}

function parseRequest(
  payload: string,
  raw: string,
  options: SourceOptions,
): DecisionRequest | null {
  try {
    return JSON.parse(payload) as DecisionRequest;
  } catch (error) {
    options.onError?.(raw, error);
    if (options.strict ?? true) throw error;
    return null;
  }
}

export async function* fromQueue<T>(queue: AsyncIterable<T | null>): AsyncIterable<T> {
  for await (const item of queue) {
    if (item === null) return;
    yield item;
  }
}

export async function* fromSync<T>(items: Iterable<T>): AsyncIterable<T> {
  for (const item of items) yield item;
}

async function* iterLines(
  lines: AsyncIterable<string> | Iterable<string>,
): AsyncIterable<string> {
  if (Symbol.asyncIterator in lines) {
    for await (const line of lines as AsyncIterable<string>) yield line;
  } else {
    for (const line of lines as Iterable<string>) yield line;
  }
}

export async function* fromNdjson(
  lines: AsyncIterable<string> | Iterable<string>,
  options: SourceOptions = {},
): AsyncIterable<DecisionRequest> {
  for await (const line of iterLines(lines)) {
    const text = line.trim();
    if (!text) continue;
    const request = parseRequest(text, text, options);
    if (request) yield request;
  }
}

export async function* fromSse(
  lines: AsyncIterable<string> | Iterable<string>,
  options: SourceOptions = {},
): AsyncIterable<DecisionRequest> {
  let data: string[] = [];
  for await (const line of iterLines(lines)) {
    if (line.startsWith("data:")) {
      data.push(line.slice(5).trim());
    } else if (!line.trim() && data.length) {
      const raw = data.join("\n");
      const request = parseRequest(raw, raw, options);
      if (request) yield request;
      data = [];
    }
  }
  if (data.length) {
    const raw = data.join("\n");
    const request = parseRequest(raw, raw, options);
    if (request) yield request;
  }
}
