/** Keep an experience snapshot between turns without owning a database. */
import { ExperienceState, InMemoryStateStore } from "../../../packages/typescript/laix/src/index.ts";

const store = new InMemoryStateStore();
const state = new ExperienceState("weekly review", "decide");
store.save("review-1", state);
const loaded = store.load("review-1");
store.delete("review-1");
console.log(loaded?.phase, store.load("review-1") === null);
