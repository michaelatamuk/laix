package dev.laix.examples.appkit.execute

import dev.laix.decision.appkit.audit.Proposal
import dev.laix.decision.appkit.audit.apply
import dev.laix.decision.appkit.audit.approve
import dev.laix.decision.appkit.audit.createRecord
import dev.laix.decision.appkit.audit.markExecuted
import dev.laix.decision.appkit.audit.reject
import dev.laix.decision.appkit.audit.undo
import dev.laix.decision.appkit.audit.verify
import dev.laix.decision.appkit.execution.ApprovalRequired
import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.execution.ExecutionStep
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.Verb
import dev.laix.examples.AT
import dev.laix.examples.summarize

private fun sendDecision(): Decision =
    Decision(
        verb = Verb.ACT,
        confidence = 0.9,
        reasonCode = "act",
        rationale = "send the report",
        actionId = "send",
    )

/** Execute one action through a host handler and keep the receipt. */
fun execution(): String {
    val bridge = ExecutionBridge()
    bridge.register("send_report", { _, _ -> mapOf("sent" to true, "channel" to "email") })
    val receipt = bridge.execute(
        decision = sendDecision(),
        action = ActionOption("send", Verb.ACT, "send_report"),
        actor = "agent",
    )
    return "status=${receipt.status} actor=${receipt.actor} detail=${receipt.detail}"
}

/** The same idempotency key returns a duplicate receipt instead of sending twice. */
fun idempotentExecution(): String {
    val bridge = ExecutionBridge()
    bridge.register("send_report", { _, _ -> mapOf("sent" to true) })
    val action = ActionOption("send", Verb.ACT, "send_report")
    val first = bridge.execute(sendDecision(), action, actor = "agent", idempotencyKey = "send-1")
    val second = bridge.execute(sendDecision(), action, actor = "agent", idempotencyKey = "send-1")
    return "first=${first.status} second=${second.status} original=${second.detail["original"] != null}"
}

/** Two steps: the second fails, so the first is compensated. */
fun executionSaga(): String {
    val bridge = ExecutionBridge()
    bridge.register("reserve", { _, _ -> mapOf("reserved" to true) })
    val steps = listOf(
        ExecutionStep(
            action = ActionOption("reserve", Verb.ACT, "reserve"),
            compensate = { mapOf("released" to true) },
        ),
        ExecutionStep(action = ActionOption("charge", Verb.ACT, "charge")),
    )
    val result = bridge.runSteps(steps)
    return "completed=${result.completed} compensated=${result.compensated} error=${result.error}"
}

/** A destructive decision needs an approver before the handler runs. */
fun approvalRequired(): String {
    val bridge = ExecutionBridge()
    bridge.register("pay_bill", { _, _ -> mapOf("paid" to true) })
    val decision = sendDecision().copy(
        actionId = "pay",
        requiresApproval = true,
        reasonCode = "approval_required",
    )
    val action = ActionOption("pay", Verb.ACT, "pay_bill")
    val refused = try {
        bridge.execute(decision, action, actor = "agent")
        "unexpected execution"
    } catch (exception: ApprovalRequired) {
        "refused: ${exception.message}"
    }
    val executed = bridge.execute(decision, action, actor = "agent", approver = "lead")
    return "$refused then ${executed.status} approvedBy=${executed.approvedBy}"
}

/** Seal a decision record, approve it, execute it, undo it and verify the hash. */
fun decisionRecord(): String {
    var record = createRecord(
        title = "Pay invoice 4832",
        decision = "Pay the invoice",
        evidence = listOf(EvidenceRef(id = "invoice-4832", kind = "document", source = "billing")),
        recordId = "dr-example",
        now = AT,
    )
    record = approve(record, by = "lead", note = "checked")
    val approvedHash = record.hash
    record = markExecuted(record, by = "agent")
    record = undo(record, by = "lead")
    return "status=${record.status} verified=${verify(record)} " +
        "hashChanged=${record.hash != approvedHash} audit=${record.audit.size}"
}

/** A proposal is the app-facing approval lifecycle. */
fun proposal(): String {
    var proposal = Proposal(id = "p-1", title = "Pay invoice", summary = "Pay invoice 4832")
    proposal = approve(proposal, by = "lead", at = AT)
    proposal = apply(proposal, at = "2026-11-01T10:05:00+00:00")
    val applied = proposal.status
    proposal = undo(proposal, at = "2026-11-01T10:06:00+00:00")
    val rejected = reject(Proposal(id = "p-2", title = "Refund", summary = "Refund the order"), by = "lead", at = AT)
    return "applied=$applied final=${proposal.status} rejected=${rejected.status}"
}
