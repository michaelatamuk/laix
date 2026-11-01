export interface Detection {
  id: string;
  detector: string;
  kind: string;
  subject: string;
  at: string;
  confidence?: number;
  severity?: string;
  payload?: Record<string, unknown>;
}

export interface PerceptionEvent {
  subject: string;
  at: string;
  payload?: Record<string, unknown>;
}

export interface PerceptionFrame {
  subject: string;
  at: string;
  detections: Detection[];
  allowed: string[];
  skipped: Array<{ name: string; reason: string; gain: number }>;
  uncertainty: number;
  deepCalls: number;
  cost: number;
  toDict(): Record<string, unknown>;
}

export interface Detector {
  name: string;
  tier?: "cheap" | "deep";
  cost?: number;
  latencyMs?: number;
  informationGain?: number;
  detect(event: PerceptionEvent): Detection[];
}
