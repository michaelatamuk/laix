import type { Decision, DecisionRequest } from "../decision/contracts.ts";
import type { StreamSession } from "./streaming.ts";

export interface StreamBenchResult {
  decisions: Decision[];
  elapsedMs: number;
  throughputPerSecond: number;
  stats: Record<string, number>;
}

export function runStreamBench(
  session: StreamSession,
  requests: Iterable<DecisionRequest>,
): StreamBenchResult {
  const started = performance.now();
  const decisions = session.replay(requests);
  const elapsedMs = performance.now() - started;
  return {
    decisions,
    elapsedMs: Number(elapsedMs.toFixed(3)),
    throughputPerSecond: elapsedMs > 0 ? Number(((decisions.length / elapsedMs) * 1000).toFixed(3)) : 0,
    stats: session.stats.snapshot(),
  };
}
