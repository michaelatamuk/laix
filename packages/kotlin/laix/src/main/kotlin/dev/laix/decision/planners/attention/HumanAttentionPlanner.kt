package dev.laix.decision.planners.attention

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.approvalRequired
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.util.Locale

/** A movable human-attention budget shared across decisions. */
class HumanAttentionBudget(
    val total: Double = 1.0,
    var spent: Double = 0.0,
) {
    init {
        require(total >= 0) { "attention budget total must not be negative" }
        require(spent >= 0) { "attention budget spent must not be negative" }
    }

    fun remaining(): Double = maxOf(0.0, total - spent)

    fun spend(amount: Double): Double {
        require(amount >= 0) { "attention spend must not be negative" }
        spent = minOf(total, spent + amount)
        return remaining()
    }

    fun toMap(): Map<String, Double> = linkedMapOf("total" to total, "spent" to spent)

    companion object {
        fun fromMap(payload: Map<String, Any?>): HumanAttentionBudget =
            HumanAttentionBudget(
                total = (payload["total"] as? Number)?.toDouble() ?: 1.0,
                spent = (payload["spent"] as? Number)?.toDouble() ?: 0.0,
            )
    }
}

/** The human-attention cost of one option. */
@ConsistentCopyVisibility
data class HumanAttentionEffect private constructor(
    val interruptCost: Double,
    val requiresApproval: Boolean,
    val escalates: Boolean,
    val interactive: Boolean,
    val approvalState: String?,
) {
    /** A comparable attention cost: interruption, approval, escalation and contact. */
    val cost: Double
        get() = interruptCost +
            (if (requiresApproval) 0.5 else 0.0) +
            (if (escalates) 0.5 else 0.0) +
            (if (interactive) 0.5 else 0.0)

    val requiresAttention: Boolean
        get() = cost > 0.0 || requiresApproval || escalates

    companion object {
        operator fun invoke(
            interruptCost: Double = 0.0,
            requiresApproval: Boolean = false,
            escalates: Boolean = false,
            interactive: Boolean = false,
            approvalState: String? = null,
        ): HumanAttentionEffect {
            @Suppress("UNUSED_VARIABLE")
            val normalized = clamp(interruptCost)
            return create(normalized, requiresApproval, escalates, interactive, approvalState)
        }

        private fun create(
            interruptCost: Double,
            requiresApproval: Boolean,
            escalates: Boolean,
            interactive: Boolean,
            approvalState: String?,
        ): HumanAttentionEffect =
            HumanAttentionEffect(
                interruptCost = interruptCost,
                requiresApproval = requiresApproval,
                escalates = escalates,
                interactive = interactive,
                approvalState = approvalState,
            )
    }
}

/** How much each kind of human attention costs. */
data class HumanAttentionWeights(
    val interrupt: Double = 0.4,
    val approval: Double = 0.25,
    val escalation: Double = 0.3,
    val exhausted: Double = 1.0,
) {
    init {
        for ((name, value) in listOf(
            "interrupt" to interrupt,
            "approval" to approval,
            "escalation" to escalation,
            "exhausted" to exhausted,
        )) {
            require(value >= 0) { "attention weight '$name' must not be negative" }
        }
    }
}

/** The utility and attention parts of one option's score. */
data class HumanAttentionScore(
    val utility: Double,
    val humanAttention: Double,
    val total: Double,
    val effect: HumanAttentionEffect,
    val remaining: Double,
    val blocked: String? = null,
)

/** Read an option's human-attention cost from its fields and `params`. */
fun humanAttentionEffect(
    option: ActionOption,
    approval: Boolean = false,
    approvalState: String? = null,
): HumanAttentionEffect {
    val params = option.params
    val payload = (params["attention"] as? Map<*, *>) ?: params
    val interrupt = when (val raw = payload["interrupt_cost"] ?: option.interruptCost) {
        is Number -> raw.toDouble()
        is String -> raw.toDoubleOrNull() ?: option.interruptCost
        else -> option.interruptCost
    }
    var requiresApproval = approval ||
        (payload["requires_approval"]?.let { truthyApproval(it) }
            ?: (option.requiresApproval || option.destructive))
    when (approvalState) {
        "approved" -> requiresApproval = false
        "pending", "rejected" -> requiresApproval = true
    }
    val escalates = payload["escalates"]?.let { truthyApproval(it) } ?: (option.verb == Verb.ESCALATE)
    return HumanAttentionEffect(
        interruptCost = interrupt,
        requiresApproval = requiresApproval,
        escalates = escalates,
        interactive = option.verb in setOf(Verb.ASK, Verb.GUIDE),
        approvalState = approvalState,
    )
}

/** Read the host's approval state for one option, if it supplied one. */
fun approvalState(problem: PlannerInput, option: ActionOption): String? {
    val raw = problem.attributes["approvals"]
    if (raw is Map<*, *>) {
        val value = raw[option.id] ?: raw[option.name] ?: return null
        return when (value) {
            is Boolean -> if (value) "approved" else "rejected"
            else -> value.toString()
        }
    }
    if (raw is Iterable<*>) {
        for (item in raw) {
            val name: Any?
            val status: Any?
            if (item is Map<*, *>) {
                name = item["action_id"] ?: item["action_name"]
                status = item["status"] ?: item["approved"]?.let {
                    if (truthyApproval(it)) "approved" else "rejected"
                }
            } else {
                continue
            }
            if ((name == option.id || name == option.name) && status != null) {
                return status.toString()
            }
        }
    }
    return null
}

/** Choose the option with the best utility plus human-attention cost. */
class HumanAttentionPlanner(
    private val model: UtilityModel = UtilityModel(),
    val weights: HumanAttentionWeights = HumanAttentionWeights(),
) : Planner {
    val name: String = "human-attention.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model)
        val remaining = remaining(problem)
        val approval = approvalRequired(problem)
        val rows = options.map { option ->
            val state = approvalState(problem, option)
            val score = scoreOption(option, activeModel, weights, remaining, approval, state)
            val blocker = constraintBlocker(problem, option)
            Row(
                option = option,
                score = score,
                feasible = activeModel.feasible(option) && blocker == null && score.blocked == null,
                blocker = score.blocked ?: blocker,
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            if (rows.any { it.blocker == "approval rejected" }) {
                return wait(
                    "approval_rejected",
                    "every remaining option was rejected or needs more attention",
                )
            }
            return wait(
                "human_attention_budget_exhausted",
                "every option needs more human attention than is left",
            )
        }

        val ranked = feasible.sortedWith(compareBy({ -it.score.total }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.score?.total

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.score.total, second),
            reasonCode = "human_attention_aware",
            rationale = format(
                "%s balances utility %.3f and attention cost %+.3f",
                best.option.id,
                best.score.utility,
                best.score.humanAttention,
            ),
            actionId = best.option.id,
            requiresApproval = best.score.effect.requiresApproval,
            reversible = best.option.reversible,
            score = best.score.total,
            alternatives = alternatives(rows, best.option.id),
            attributes = linkedMapOf(
                "utility" to best.score.utility,
                "human_attention_score" to best.score.humanAttention,
                "human_attention_cost" to best.score.effect.cost,
                "human_attention_remaining" to best.score.remaining,
                "human_attention_budget_blocked" to best.score.blocked,
                "approval_state" to best.score.effect.approvalState,
            ),
        )
    }

    internal fun scoreOption(
        option: ActionOption,
        model: UtilityModel,
        weights: HumanAttentionWeights,
        remaining: Double,
        approval: Boolean,
        state: String?,
    ): HumanAttentionScore {
        val effect = humanAttentionEffect(option, approval = approval, approvalState = state)
        val blocked = when {
            state == "rejected" -> "approval rejected"
            effect.requiresAttention && effect.cost > remaining ->
                "human attention budget exhausted"
            else -> null
        }
        val attention =
            -weights.interrupt * effect.interruptCost -
                weights.approval * (if (effect.requiresApproval) 1.0 else 0.0) -
                weights.escalation * (if (effect.escalates) 1.0 else 0.0) -
                weights.exhausted * (if (blocked != null) 1.0 else 0.0)
        val utility = model.score(option)
        return HumanAttentionScore(
            utility = round6(utility),
            humanAttention = round6(attention),
            total = round6(utility + attention),
            effect = effect,
            remaining = maxOf(0.0, remaining - effect.cost),
            blocked = blocked,
        )
    }

    private fun alternatives(rows: List<Row>, bestId: String): List<Map<String, Any?>> =
        rows
            .filter { it.option.id != bestId }
            .map { row ->
                val reason = when {
                    row.blocker != null -> "blocked by ${row.blocker}"
                    !row.feasible -> "outside the hard limits"
                    else -> "lower attention-adjusted score"
                }
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.score.utility,
                    "human_attention" to row.score.humanAttention,
                    "total" to row.score.total,
                    "rejected_because" to reason,
                )
            }
            .sortedWith(compareBy({ -(it["total"] as Double) }, { it["action_id"] as String }))

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }

    private fun wait(reasonCode: String, rationale: String): PlannerResult =
        PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = reasonCode,
            rationale = rationale,
            score = 0.0,
        )

    private fun format(pattern: String, vararg args: Any): String =
        String.format(Locale.ROOT, pattern, *args)

    private data class Row(
        val option: ActionOption,
        val score: HumanAttentionScore,
        val feasible: Boolean,
        val blocker: String?,
    )

    companion object {
        internal fun remaining(problem: PlannerInput): Double {
            val attributes = problem.attributes
            val raw = attributes["human_attention_budget"] ?: 1.0
            val base = when (raw) {
                is HumanAttentionBudget -> raw.remaining()
                is Map<*, *> -> {
                    val total = (raw["total"] as? Number)?.toDouble() ?: 1.0
                    val spent = (raw["spent"] as? Number)?.toDouble() ?: 0.0
                    total - spent
                }
                else -> {
                    val numeric = when (raw) {
                        is Number -> raw.toDouble()
                        is String -> raw.toDoubleOrNull()
                        else -> null
                    } ?: 1.0
                    val spent = when (val value = attributes["human_attention_spent"] ?: 0.0) {
                        is Number -> value.toDouble()
                        is String -> value.toDoubleOrNull() ?: 0.0
                        else -> 0.0
                    }
                    numeric - spent
                }
            }
            val override = when (val value = attributes["human_attention_remaining"]) {
                is Number -> value.toDouble()
                is String -> value.toDoubleOrNull()
                else -> null
            }
            return maxOf(0.0, override ?: base)
        }
    }
}

private fun truthyApproval(value: Any?): Boolean =
    when (value) {
        null -> false
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        is String -> value.trim().lowercase() in setOf("1", "true", "yes", "approved", "required", "on")
        is Collection<*> -> value.isNotEmpty()
        is Map<*, *> -> value.isNotEmpty()
        else -> true
    }
