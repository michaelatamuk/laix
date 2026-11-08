export function rewardForLabel(label: string): number | null {
  return ({ helped: 1, neutral: 0.5, hurt: 0 } as Record<string, number>)[(label ?? "").trim().toLowerCase()] ?? null;
}
