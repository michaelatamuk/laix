package dev.laix.decision.appkit.execution

import dev.laix.decision.appkit.records.ExecutionReceipt
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.newId

/** A host skill that performs one action. */
typealias Handler = (ActionOption, Map<String, Any?>) -> Map<String, Any?>

/** Raised when a destructive decision has no approver. */
class ApprovalRequired(message: String) : RuntimeException(message)

/** How many times to retry a failed handler, and how long to wait. */
data class RetryPolicy(
    val attempts: Int = 1,
    val backoffSeconds: Double = 0.0,
    val maxBackoffSeconds: Double = 30.0,
) {
    init {
        require(attempts >= 1) { "attempts must be at least 1" }
        require(backoffSeconds >= 0 && maxBackoffSeconds >= 0) { "backoff must not be negative" }
    }

    /** Exponential backoff after a failed attempt, capped. */
    fun delay(attempt: Int): Double {
        if (backoffSeconds <= 0) return 0.0
        return minOf(backoffSeconds * Math.pow(2.0, (attempt - 1).toDouble()), maxBackoffSeconds)
    }
}

/** One forward action and its optional compensation. */
data class ExecutionStep(
    val action: ActionOption,
    val decision: Decision? = null,
    val actor: String? = null,
    val approver: String? = null,
    val context: Map<String, Any?> = emptyMap(),
    val idempotencyKey: String? = null,
    val compensate: ((ExecutionReceipt) -> Map<String, Any?>)? = null,
)

/** The outcome of a multi-step execution, including every receipt. */
data class ExecutionSagaResult(
    val completed: List<String>,
    val compensated: List<String>,
    val receipts: List<ExecutionReceipt>,
    val error: String? = null,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "completed" to completed,
            "compensated" to compensated,
            "receipts" to receipts.map { it.toMap() },
            "error" to error,
        )
}

/**
 * Execution bridge: approval, execution, cancellation, recovery and receipts.
 *
 * LAIX decides; the host executes. The bridge is a thin, auditable state machine
 * around named host skills.
 */
class ExecutionBridge(
    handlers: Map<String, Handler> = emptyMap(),
    undoHandlers: Map<String, Handler> = emptyMap(),
) {
    val handlers: MutableMap<String, Handler> = LinkedHashMap(handlers)
    val undoHandlers: MutableMap<String, Handler> = LinkedHashMap(undoHandlers)
    val receipts: LinkedHashMap<String, ExecutionReceipt> = LinkedHashMap()
    private val byKey: LinkedHashMap<String, String> = LinkedHashMap()

    fun register(name: String, handler: Handler, undo: Handler? = null) {
        handlers[name] = handler
        if (undo != null) undoHandlers[name] = undo
    }

    fun canHandle(name: String): Boolean = handlers.containsKey(name)

    fun canUndo(name: String): Boolean = undoHandlers.containsKey(name)

    fun execute(
        decision: Decision,
        action: ActionOption?,
        actor: String,
        approver: String? = null,
        context: Map<String, Any?>? = null,
        idempotencyKey: String? = null,
        retry: RetryPolicy? = null,
    ): ExecutionReceipt {
        if (idempotencyKey != null && byKey.containsKey(idempotencyKey)) {
            val original = receipts.getValue(byKey.getValue(idempotencyKey))
            return store(
                ExecutionReceipt(
                    id = newId("RCT"),
                    decisionId = decision.decisionId,
                    actionName = action?.name ?: "",
                    status = "duplicate",
                    actor = actor,
                    detail = mapOf("original" to original.id),
                    approvedBy = approver,
                    idempotencyKey = idempotencyKey,
                ),
            )
        }
        if (action == null) {
            return store(
                ExecutionReceipt(
                    id = newId("RCT"),
                    decisionId = decision.decisionId,
                    actionName = "",
                    status = "refused",
                    actor = actor,
                    error = "decision has no action to execute",
                    idempotencyKey = idempotencyKey,
                ),
            )
        }
        if (decision.requiresApproval && approver.isNullOrEmpty()) {
            throw ApprovalRequired("${action.name} requires human approval")
        }
        val handler = handlers[action.name]
        if (handler == null) {
            return store(
                ExecutionReceipt(
                    id = newId("RCT"),
                    decisionId = decision.decisionId,
                    actionName = action.name,
                    status = "failed",
                    actor = actor,
                    error = "no handler registered for ${action.name}",
                    approvedBy = approver,
                    idempotencyKey = idempotencyKey,
                ),
            )
        }
        val policy = retry ?: RetryPolicy()
        var detail: Map<String, Any?> = emptyMap()
        for (attempt in 1..policy.attempts) {
            try {
                detail = handler(action, LinkedHashMap(context ?: emptyMap()))
                if (attempt > 1) detail = detail + mapOf("attempts" to attempt)
                break
            } catch (exception: Exception) {
                if (attempt < policy.attempts) {
                    val delay = policy.delay(attempt)
                    if (delay > 0) Thread.sleep((delay * 1000).toLong())
                    continue
                }
                return store(
                    ExecutionReceipt(
                        id = newId("RCT"),
                        decisionId = decision.decisionId,
                        actionName = action.name,
                        status = "failed",
                        actor = actor,
                        detail = mapOf("attempts" to attempt),
                        error = "${exception::class.simpleName}: ${exception.message}",
                        approvedBy = approver,
                        idempotencyKey = idempotencyKey,
                    ),
                )
            }
        }
        val receipt = store(
            ExecutionReceipt(
                id = newId("RCT"),
                decisionId = decision.decisionId,
                actionName = action.name,
                status = "executed",
                actor = actor,
                detail = detail,
                approvedBy = approver,
                idempotencyKey = idempotencyKey,
            ),
        )
        if (idempotencyKey != null) byKey[idempotencyKey] = receipt.id
        return receipt
    }

    /** Execute steps in order and compensate completed ones on failure. */
    fun runSteps(steps: List<ExecutionStep>, actor: String = "system"): ExecutionSagaResult {
        val receipts = mutableListOf<ExecutionReceipt>()
        val completed = LinkedHashMap<String, ExecutionReceipt>()
        val failure = mutableListOf<String>()
        val sagaSteps = mutableListOf<SagaStep>()
        for ((index, step) in steps.withIndex()) {
            val key = index.toString()
            val decision = step.decision ?: Decision(
                verb = step.action.verb,
                confidence = 1.0,
                reasonCode = "execution_step",
                rationale = step.action.name,
            )
            val forward: () -> Map<String, Any?> = {
                val receipt = execute(
                    decision = decision,
                    action = step.action,
                    actor = step.actor ?: actor,
                    approver = step.approver,
                    context = step.context,
                    idempotencyKey = step.idempotencyKey,
                )
                receipts += receipt
                if (receipt.status == "executed" || receipt.status == "duplicate") {
                    completed[key] = receipt
                    receipt.detail
                } else {
                    val message = receipt.error ?: "${step.action.name} did not execute"
                    failure += message
                    throw RuntimeException(message)
                }
            }
            val compensate: (() -> Map<String, Any?>)? = when {
                step.compensate != null -> fun(): Map<String, Any?> {
                    val receipt = completed[key] ?: return emptyMap()
                    return step.compensate.invoke(receipt)
                }
                canUndo(step.action.name) -> fun(): Map<String, Any?> {
                    val receipt = completed[key] ?: return emptyMap()
                    return undo(receipt.id, actor).detail
                }
                else -> null
            }
            sagaSteps += SagaStep(step.action.name, forward, compensate)
        }
        val result = Saga().run(sagaSteps)
        return ExecutionSagaResult(
            completed = result.completed,
            compensated = result.compensated,
            receipts = receipts,
            error = failure.firstOrNull() ?: result.error,
        )
    }

    fun refuse(
        decision: Decision,
        action: ActionOption?,
        actor: String,
        reason: String,
    ): ExecutionReceipt =
        store(
            ExecutionReceipt(
                id = newId("RCT"),
                decisionId = decision.decisionId,
                actionName = action?.name ?: "",
                status = "refused",
                actor = actor,
                error = reason,
            ),
        )

    fun cancel(receiptId: String, actor: String, reason: String = ""): ExecutionReceipt {
        val receipt = get(receiptId)
        require(receipt.status in setOf("pending", "approved")) {
            "cannot cancel a receipt that is ${receipt.status}"
        }
        return store(
            receipt.copy(
                status = "cancelled",
                actor = actor,
                detail = receipt.detail + mapOf("cancel_reason" to reason),
            ),
        )
    }

    fun undo(receiptId: String, actor: String): ExecutionReceipt {
        val receipt = get(receiptId)
        require(receipt.status == "executed") {
            "cannot undo a receipt that is ${receipt.status}"
        }
        val handler = undoHandlers[receipt.actionName]
            ?: throw IllegalArgumentException("no undo handler for ${receipt.actionName}")
        val detail = try {
            handler(
                ActionOption(id = receipt.id, verb = Verb.ACT, name = receipt.actionName),
                mapOf("receipt" to receipt.toMap()),
            )
        } catch (exception: Exception) {
            throw IllegalArgumentException(
                "undo failed: ${exception::class.simpleName}: ${exception.message}",
            )
        }
        return store(
            receipt.copy(
                status = "undone",
                actor = actor,
                detail = receipt.detail + mapOf("undo" to detail),
                previousState = receipt.detail,
            ),
        )
    }

    /** Record that the action may have happened; do not retry blindly. */
    fun markUnknown(receiptId: String, actor: String, reason: String = ""): ExecutionReceipt {
        val receipt = get(receiptId)
        return store(
            receipt.copy(
                status = "unknown",
                actor = actor,
                detail = receipt.detail + mapOf("unknown_reason" to reason),
            ),
        )
    }

    /** Resolve an unknown outcome with provider evidence. */
    fun reconcile(
        receiptId: String,
        actor: String,
        status: String,
        detail: Map<String, Any?> = emptyMap(),
    ): ExecutionReceipt {
        require(status in setOf("executed", "failed", "unknown")) {
            "cannot reconcile to $status"
        }
        val receipt = get(receiptId)
        val reconciled = receipt.copy(
            status = status,
            actor = actor,
            detail = receipt.detail + detail,
        )
        if (status == "executed" && reconciled.idempotencyKey != null) {
            byKey[reconciled.idempotencyKey] = reconciled.id
        }
        return store(reconciled)
    }

    fun get(receiptId: String): ExecutionReceipt =
        receipts[receiptId] ?: throw NoSuchElementException(receiptId)

    /** Map action name to its latest receipt status for execution-aware planning. */
    fun executionState(): Map<String, String> =
        receipts.values.associate { it.actionName to it.status }

    private fun store(receipt: ExecutionReceipt): ExecutionReceipt {
        receipts[receipt.id] = receipt
        return receipt
    }
}
