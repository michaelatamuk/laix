import { Saga } from "../../../../packages/typescript/laix/src/index.ts";

const log: string[] = [];
const result = new Saga().run([
  {
    name: "first",
    forward: () => {
      log.push("first");
      return {};
    },
    compensate: () => {
      log.push("undo first");
      return {};
    },
  },
  {
    name: "second",
    forward: () => {
      log.push("second");
      throw new Error("boom");
    },
  },
]);

console.log(result.completed.join(","), result.compensated.join(","), result.error);
