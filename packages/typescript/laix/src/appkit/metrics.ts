import type { StreamStats } from "./streaming.ts";

export function prometheus(stats: StreamStats, prefix = "laix_stream"): string {
  const lines: string[] = [];
  for (const [key, value] of Object.entries(stats.snapshot())) {
    const name = `${prefix}_${key}`;
    lines.push(`# TYPE ${name} gauge`);
    lines.push(`${name} ${value}`);
  }
  return lines.join("\n") + "\n";
}
