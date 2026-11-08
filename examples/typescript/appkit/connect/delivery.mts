/** LAIX decides to show something. The app owns the transport. */
import { NullDelivery } from "../../../../packages/typescript/laix/src/index.ts";

const receipt = new NullDelivery().deliver({ decisionId: "d-1" }, "Electricity bill due tomorrow", { channel: "email" });
console.log(receipt.status, receipt.channel);
