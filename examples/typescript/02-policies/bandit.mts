/** Outcome learning: feedback changes the next choice. */
import { BanditPolicy, DecisionClient, UCBBandit } from "../../../packages/typescript/laix/src/index.ts";

const policy = new BanditPolicy(new UCBBandit([{ id: "manual" }, { id: "automatic" }]));
const layer = new DecisionClient({ policy });
const request = { subject: "pick a mode", at: "2026-11-01T10:00:00Z" };

const first = layer.decide(request)[0];
policy.record("manual", 0);
policy.record("automatic", 1);
const second = layer.decide(request)[0];

console.log(first.actionId, second.actionId, policy.bandit.mean("automatic").toFixed(2));
