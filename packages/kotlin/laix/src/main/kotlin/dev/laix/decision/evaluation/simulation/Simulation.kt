package dev.laix.decision.evaluation.simulation

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.support.iso
import dev.laix.decision.support.round
import java.util.SplittableRandom
import kotlin.math.abs

/** One step in a simulated trace. */
data class SimulationStep(
    val step: Int,
    val state: String,
    val action: String?,
    val reward: Double,
    val nextState: String,
)

/** What one planner did in one scenario. */
data class SimulationResult(
    val scenario: String,
    val steps: List<SimulationStep>,
    val totalReward: Double,
    val finalState: String,
) {
    fun summary(): Map<String, Any?> =
        linkedMapOf(
            "scenario" to scenario,
            "steps" to steps.size,
            "total_reward" to round(totalReward, 6),
            "final_state" to finalState,
        )
}

/** One planner's result on one scenario. */
data class PlannerBenchmarkRow(
    val planner: String,
    val scenario: String,
    val totalReward: Double,
    val steps: Int,
    val optimalityGap: Double?,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "planner" to planner,
            "scenario" to scenario,
            "total_reward" to round(totalReward, 6),
            "steps" to steps,
            "optimality_gap" to optimalityGap,
        )
}

/** One named simulator, with an optional known optimum. */
data class Scenario(
    val name: String,
    val simulator: Simulator,
    val optimum: Double? = null,
) {
    fun run(planner: Planner): SimulationResult {
        val result = simulator.run(planner)
        return SimulationResult(
            scenario = name,
            steps = result.steps,
            totalReward = result.totalReward,
            finalState = result.finalState,
        )
    }
}

/** Planner scores across a set of scenarios. */
data class SimulationReport(
    val rows: List<PlannerBenchmarkRow>,
) {
    fun summary(): Map<String, Map<String, Any?>> {
        val buckets = LinkedHashMap<String, MutableList<PlannerBenchmarkRow>>()
        for (row in rows) buckets.getOrPut(row.planner) { mutableListOf() } += row
        return buckets.toSortedMap().mapValues { (_, items) ->
            linkedMapOf<String, Any?>(
                "runs" to items.size,
                "mean_reward" to round(items.sumOf { it.totalReward } / items.size, 6),
                "mean_gap" to round(items.sumOf { it.optimalityGap ?: 0.0 } / items.size, 6),
            )
        }
    }

    fun best(): String? {
        val summary = summary()
        if (summary.isEmpty()) return null
        return summary.keys.sortedWith(
            compareBy { planner -> -(summary.getValue(planner).getValue("mean_reward") as Double) },
        ).first()
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "rows" to rows.map { it.toMap() },
            "summary" to summary(),
            "best" to best(),
        )
}

/** A deterministic environment a planner can be run in. */
class Simulator(
    val step: (String, String) -> Pair<String, Double>,
    actions: List<String>,
    val start: String,
    val horizon: Int = 10,
    val name: String = "scenario",
    val randomStep: ((String, String, SplittableRandom) -> Pair<String, Double>)? = null,
    val seed: Int? = null,
) {
    init {
        require(actions.isNotEmpty()) { "a simulator needs at least one action" }
        require(horizon >= 0) { "horizon must not be negative" }
    }

    val actions: List<String> = actions.toList()

    fun run(planner: Planner): SimulationResult {
        var state = start
        val steps = mutableListOf<SimulationStep>()
        var total = 0.0
        val rng = if (randomStep != null && seed != null) SplittableRandom(seed.toLong()) else null
        for (index in 0 until horizon) {
            val problem = PlannerInput(
                subject = name,
                at = iso(),
                attributes = mapOf("state" to state),
            )
            val plan = planner.solve(problem)
            val action = plan.actionId
            if (action == null || action !in actions) {
                steps += SimulationStep(index, state, action, 0.0, state)
                break
            }
            val (nextState, reward) = if (randomStep != null && rng != null) {
                randomStep.invoke(state, action, rng)
            } else {
                step(state, action)
            }
            steps += SimulationStep(index, state, action, reward, nextState)
            total += reward
            state = nextState
        }
        return SimulationResult(
            scenario = name,
            steps = steps,
            totalReward = round(total, 6),
            finalState = state,
        )
    }

    companion object {
        /**
         * Build a simulator from an MDP.
         *
         * Without [seed] the run follows the most likely transition and is
         * repeatable. With [seed] it samples transitions, and each run resets
         * the generator so the same seed gives the same trace.
         */
        fun fromMdp(
            model: MdpModel,
            start: String? = null,
            seed: Int? = null,
        ): Simulator {
            val resolvedStart = start ?: model.start
            val horizon = model.horizon ?: 10

            fun step(state: String, action: String): Pair<String, Double> {
                val rows = model.outgoing(state, action)
                if (rows.isEmpty()) return state to 0.0
                val chosen = rows.sortedWith(
                    compareBy({ -it.probability }, { it.nextState }),
                ).first()
                return chosen.nextState to chosen.reward
            }

            fun randomStep(state: String, action: String, rng: SplittableRandom): Pair<String, Double> {
                val rows = model.outgoing(state, action)
                if (rows.isEmpty()) return state to 0.0
                val roll = rng.nextDouble()
                var cumulative = 0.0
                for (item in rows) {
                    cumulative += item.probability
                    if (roll <= cumulative) return item.nextState to item.reward
                }
                val last = rows.last()
                return last.nextState to last.reward
            }

            return Simulator(
                step = ::step,
                actions = model.actions,
                start = resolvedStart,
                horizon = horizon,
                name = "mdp:${model.start}",
                randomStep = if (seed != null) ::randomStep else null,
                seed = seed,
            )
        }
    }
}

/** Run every planner on every scenario and report reward and optimality gap. */
fun comparePlanners(
    planners: Map<String, Planner>,
    scenarios: List<Scenario>,
): SimulationReport {
    val rows = mutableListOf<PlannerBenchmarkRow>()
    for (scenario in scenarios) {
        for ((name, planner) in planners) {
            val result = scenario.run(planner)
            val gap = scenario.optimum?.let { optimum ->
                round(
                    maxOf(0.0, (optimum - result.totalReward) / maxOf(abs(optimum), 1e-9)),
                    6,
                )
            }
            rows += PlannerBenchmarkRow(
                planner = name,
                scenario = scenario.name,
                totalReward = result.totalReward,
                steps = result.steps.size,
                optimalityGap = gap,
            )
        }
    }
    return SimulationReport(rows)
}

/**
 * Build deterministic scenarios with a known optimum.
 *
 * Each scenario is a finite chain of states. The reward table comes from the
 * seed; the optimum is computed by backward induction.
 */
fun seededScenarios(
    seed: Int,
    count: Int = 3,
    horizon: Int = 8,
    actions: List<String> = listOf("a", "b"),
): List<Scenario> {
    require(count >= 1) { "count must be at least one" }
    require(horizon >= 1) { "horizon must be at least one" }
    val rng = SplittableRandom(seed.toLong())
    val scenarios = mutableListOf<Scenario>()
    for (index in 0 until count) {
        val table = LinkedHashMap<String, Map<String, Double>>()
        for (stepIndex in 0 until horizon) {
            val state = "s$stepIndex"
            table[state] = actions.associateWith {
                round(-1.0 + 2.0 * rng.nextDouble(), 6)
            }
        }

        fun step(state: String, action: String): Pair<String, Double> {
            val reward = table[state]?.get(action) ?: 0.0
            val indexValue = if (state.startsWith("s")) {
                state.substring(1).toIntOrNull() ?: 0
            } else {
                0
            }
            return "s${indexValue + 1}" to reward
        }

        val simulator = Simulator(
            step = ::step,
            actions = actions,
            start = "s0",
            horizon = horizon,
            name = "seeded-$seed-$index",
        )
        var best = 0.0
        for (stepIndex in 0 until horizon) {
            val state = "s$stepIndex"
            best += table[state]?.values?.maxOrNull() ?: 0.0
        }
        scenarios += Scenario(
            name = "seeded-$seed-$index",
            simulator = simulator,
            optimum = round(best, 6),
        )
    }
    return scenarios
}
