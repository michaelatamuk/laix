import type { Belief, Decision, Observation, Phase } from "../../decision/contracts.ts";
import { PHASES, clamp, confidenceBand, iso } from "../../decision/contracts.ts";

export class ExperienceState {
  subject: string;
  phase: Phase;
  goals: Record<string, unknown>[] = [];
  constraints: Record<string, unknown>[] = [];
  beliefs = new Map<string, Belief>();
  history: Record<string, unknown>[] = [];
  observations: Observation[] = [];

  constructor(subject: string, phase: Phase = "observe") {
    if (!PHASES.includes(phase)) throw new Error(`unknown phase: ${phase}`);
    this.subject = subject;
    this.phase = phase;
  }

  observe(observation: Observation, halfLifeMinutes = 720): Belief | null {
    this.observations.push(observation);
    this.history.push({ at: observation.at, event: "observed", observation: observation.id, source: observation.source });
    const proposition = observation.payload?.proposition;
    if (!proposition) return null;
    const confidence = Number(observation.payload?.confidence ?? observation.confidence ?? 0.5);
    const previous = this.beliefs.get(String(proposition));
    let merged = clamp(confidence);
    if (previous) {
      const prior = decayed(previous, observation.at, halfLifeMinutes);
      merged = clamp(0.55 * confidence + 0.45 * prior);
    }
    const belief: Belief = {
      id: String(proposition),
      proposition: String(observation.payload?.statement ?? proposition),
      confidence: merged,
      evidence: [observation.id, ...(previous?.evidence ?? [])].slice(-8),
      updatedAt: observation.at || iso(),
      expiresAt: (observation.payload?.expires_at as string | undefined) ?? null,
      source: observation.source,
    };
    this.beliefs.set(belief.id, belief);
    return belief;
  }

  setBelief(belief: Belief): Belief {
    this.beliefs.set(belief.id, belief);
    this.history.push({ at: iso(), event: "belief.updated", belief: belief.id, confidence: belief.confidence });
    return belief;
  }

  belief(id: string): Belief | null {
    return this.beliefs.get(id) ?? null;
  }

  confidence(ids?: string[]): number {
    const items = (ids ? ids.map((id) => this.beliefs.get(id)).filter(Boolean) : [...this.beliefs.values()]) as Belief[];
    if (items.length === 0) return 0;
    return clamp(Math.min(...items.map((item) => item.confidence)));
  }

  band(id: string): string {
    const item = this.beliefs.get(id);
    return item ? confidenceBand(item.confidence) : "unknown";
  }

  expire(now: Date = new Date()): string[] {
    const removed: string[] = [];
    for (const [key, item] of this.beliefs) {
      if (item.expiresAt && new Date(item.expiresAt).getTime() <= now.getTime()) {
        this.beliefs.delete(key);
        this.history.push({ at: iso(now), event: "belief.expired", belief: key, confidence: item.confidence });
        removed.push(key);
      }
    }
    return removed;
  }

  decay(now: Date = new Date(), halfLifeMinutes = 720): void {
    for (const [key, item] of this.beliefs) {
      this.beliefs.set(key, { ...item, confidence: decayed(item, iso(now), halfLifeMinutes) });
    }
  }

  advance(phase: Phase): void {
    if (!PHASES.includes(phase)) throw new Error(`unknown phase: ${phase}`);
    this.phase = phase;
    this.history.push({ at: iso(), event: "phase", phase });
  }

  record(decision: Decision, note = ""): void {
    this.history.push({ at: decision.createdAt ?? iso(), event: "decision", decision: decision.decisionId ?? "", verb: decision.verb, action: decision.actionId ?? null, note });
    this.phase = ["act", "guide", "ask"].includes(decision.verb) ? "act" : "decide";
  }

  snapshot(): Record<string, unknown> {
    return {
      subject: this.subject,
      phase: this.phase,
      goals: [...this.goals],
      constraints: [...this.constraints],
      beliefs: [...this.beliefs.values()],
      history: [...this.history],
      observations: [...this.observations],
    };
  }

  static fromSnapshot(payload: Record<string, unknown>): ExperienceState {
    const state = new ExperienceState(String(payload.subject ?? ""), (payload.phase as Phase) ?? "observe");
    state.goals = (payload.goals as Record<string, unknown>[]) ?? [];
    state.constraints = (payload.constraints as Record<string, unknown>[]) ?? [];
    for (const item of (payload.beliefs as Belief[]) ?? []) state.beliefs.set(item.id, item);
    state.history = (payload.history as Record<string, unknown>[]) ?? [];
    state.observations = (payload.observations as Observation[]) ?? [];
    return state;
  }

  toDict(): Record<string, unknown> {
    return this.snapshot();
  }
}

function decayed(belief: Belief, at: string, halfLifeMinutes: number): number {
  if (!belief.updatedAt) return belief.confidence;
  const minutes = Math.max(0, (new Date(at).getTime() - new Date(belief.updatedAt).getTime()) / 60000);
  if (!Number.isFinite(minutes) || minutes === 0) return belief.confidence;
  return clamp(belief.confidence * Math.pow(0.5, minutes / Math.max(halfLifeMinutes, 1)));
}
