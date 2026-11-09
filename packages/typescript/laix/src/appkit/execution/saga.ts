export type SagaForward = () => Record<string, unknown>;
export type SagaCompensate = () => Record<string, unknown>;

export interface SagaStep {
  name: string;
  forward: SagaForward;
  compensate?: SagaCompensate;
}

export interface SagaResult {
  completed: string[];
  compensated: string[];
  error?: string | null;
}

export class Saga {
  run(steps: SagaStep[]): SagaResult {
    const completed: SagaStep[] = [];
    try {
      for (const step of steps) {
        step.forward();
        completed.push(step);
      }
    } catch (error) {
      const compensated: string[] = [];
      for (const step of [...completed].reverse()) {
        if (!step.compensate) continue;
        try {
          step.compensate();
          compensated.push(step.name);
        } catch {
          continue;
        }
      }
      const message =
        error instanceof Error ? `${error.name}: ${error.message}` : String(error);
      return {
        completed: completed.map((item) => item.name),
        compensated,
        error: message,
      };
    }
    return { completed: completed.map((item) => item.name), compensated: [] };
  }
}
