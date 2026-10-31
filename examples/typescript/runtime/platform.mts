/** The south interface: run a skill, ask for approval, read events. */
import { InMemoryPlatform } from "../../../packages/typescript/laix/src/index.ts";

const platform = new InMemoryPlatform({ approver: () => ({ approved: true, by: "owner" }) });
platform.register("lookup", (call) => call.args?.value);
const result = platform.runSkill({ capability: "lookup", args: { value: 7 }, traceId: "tr-1" });
const events = platform.events("tr-1").map((event) => event.kind).join(",");
const approval = platform.requestApproval({ decisionId: "d-1", action: "assign" });
console.log(result, events, platform.capability("fast").level, approval.approved);
