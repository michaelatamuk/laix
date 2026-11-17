package dev.laix.decision.planners.portfolio

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.planners.commitment.commitmentEffect
import dev.laix.decision.support.truthy

/** A function that names the planner for one problem. */
fun interface PlannerSelector {
    fun select(problem: PlannerInput): String
}

/** Select a planner from a named portfolio and delegate to it. */
class PortfolioPlanner(
    planners: Map<String, Planner>,
    selector: PlannerSelector? = null,
    default: String? = null,
) : Planner {
    val name: String = "portfolio.v1"

    private val planners: Map<String, Planner>
    private val selector: PlannerSelector
    private val default: String

    init {
        require(planners.isNotEmpty()) { "a portfolio needs at least one planner" }
        this.planners = LinkedHashMap(planners)
        this.selector = selector ?: PlannerSelector { defaultSelector(it) }
        this.default = default ?: this.planners.keys.first()
        require(this.default in this.planners) { "unknown default planner: ${this.default}" }
    }

    override fun solve(problem: PlannerInput): PlannerResult {
        val selected = selector.select(problem).let { if (it in planners) it else default }
        val result = planners.getValue(selected).solve(problem)
        return result.copy(
            attributes = result.attributes + mapOf(
                "planner" to selected,
                "portfolio" to planners.keys.sorted(),
            ),
        )
    }

    companion object {
        /** The built-in routing heuristic, in priority order. */
        fun defaultSelector(problem: PlannerInput): String {
            val attributes = problem.attributes
            (attributes["planner"] as? String)?.let { return it }
            val options = problem.options
            if (truthy(attributes["commitments"]) ||
                truthy(attributes["commitment_ledger"]) ||
                truthy(attributes["commitment_graph"]) ||
                truthy(attributes["external_commitments"]) ||
                options.any {
                    commitmentEffect(it).let { effect ->
                        effect.fulfills.isNotEmpty() ||
                            effect.violates.isNotEmpty() ||
                            effect.creates.isNotEmpty()
                    }
                }
            ) {
                return "commitment"
            }
            if (truthy(attributes["requires_approval"]) ||
                options.any { it.requiresApproval || it.destructive || it.risk >= 0.5 }
            ) {
                return "execution"
            }
            if (truthy(attributes["human_attention_budget"]) ||
                truthy(attributes["attention_budget"]) ||
                truthy(attributes["approval"])
            ) {
                return "human_attention"
            }
            if (truthy(attributes["mdp_model"])) return "mdp"
            if (truthy(attributes["pomdp_model"])) return "pomdp"
            return "utility"
        }
    }
}
