import { ExecutionTimeout } from "./execution-types.ts";

export function retryDelay(attempt: number, backoffMs: number, maxBackoffMs: number): number {
  if (backoffMs <= 0) return 0;
  return Math.min(backoffMs * 2 ** (attempt - 1), maxBackoffMs);
}

export function sleepSync(ms: number): void {
  if (ms <= 0) return;
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

export function sleep(ms: number): Promise<void> {
  return ms <= 0 ? Promise.resolve() : new Promise((resolve) => setTimeout(resolve, ms));
}

export async function withTimeout<T>(work: Promise<T>, timeoutMs?: number): Promise<T> {
  if (timeoutMs === undefined) return work;
  if (timeoutMs <= 0) throw new Error("timeoutMs must be positive");
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new ExecutionTimeout(timeoutMs)), timeoutMs);
  });
  try {
    return await Promise.race([work, timeout]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}
