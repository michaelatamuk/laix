package dev.laix.decision.evaluation.bench

import dev.laix.decision.appkit.bench.runBench
import dev.laix.decision.appkit.bench.runPlannerBench
import dev.laix.decision.appkit.bench.suiteNames
import dev.laix.decision.appkit.bench.allSuites
import dev.laix.decision.evaluation.simulation.SimulationReport
import dev.laix.decision.support.toJson
import java.util.Locale
import kotlin.system.exitProcess

/** Run the LAIX decision-class bench. */
fun main(args: Array<String>) {
    exitProcess(runBenchCli(args.toList()))
}

fun runBenchCli(args: List<String>): Int {
    val suites = mutableListOf<String>()
    var planners = false
    var live = false
    var json = false
    var list = false
    var failUnder = 1.0

    var index = 0
    while (index < args.size) {
        when (args[index]) {
            "--suite" -> {
                val value = args.getOrNull(index + 1) ?: return usage()
                suites += value
                index += 2
            }
            "--planners" -> { planners = true; index++ }
            "--live" -> { live = true; index++ }
            "--json" -> { json = true; index++ }
            "--list" -> { list = true; index++ }
            "--fail-under" -> {
                failUnder = args.getOrNull(index + 1)?.toDoubleOrNull() ?: return usage()
                index += 2
            }
            else -> return usage()
        }
    }

    if (list) {
        allSuites().forEach {
            println(String.format(Locale.ROOT, "%-24s %s", it.name, it.description))
        }
        return 0
    }

    val unknown = suites.filter { it !in BENCH_SUITE_NAMES }
    if (unknown.isNotEmpty()) {
        System.err.println("laix-bench: unknown suite ${unknown.first()}")
        return 2
    }

    if (live) {
        val report = runLiveBench()
        if (json) {
            println(report.toMap().toJson(pretty = true))
        } else {
            println(report.summary())
        }
        return 0
    }

    if (planners) {
        val report = runPlannerBench()
        if (json) {
            println(report.toMap().toJson(pretty = true))
        } else {
            printPlannerTable(report)
        }
        return 0
    }

    val report = runBench(suites.ifEmpty { null })
    if (json) {
        println(report.toMap().toJson(pretty = true))
    } else {
        printTable(report)
    }
    return if (report.agreement >= failUnder) 0 else 1
}

private fun printTable(report: dev.laix.decision.appkit.bench.BenchReport) {
    println(String.format(Locale.ROOT, "%-24s %6s %7s %10s", "suite", "cases", "passed", "agreement"))
    println("-".repeat(51))
    for ((name, row) in report.bySuite()) {
        println(
            String.format(
                Locale.ROOT,
                "%-24s %6d %7d %10.3f",
                name,
                row["cases"],
                row["passed"],
                row["agreement"],
            ),
        )
    }
    println("-".repeat(51))
    println(
        String.format(
            Locale.ROOT,
            "%-24s %6d %7d %10.3f",
            "overall",
            report.total,
            report.passed,
            report.agreement,
        ),
    )
    val failed = report.rows.filter { !it.passed }
    if (failed.isNotEmpty()) {
        println()
        failed.forEach {
            println("FAIL ${it.suite}/${it.case}: ${it.mismatches.joinToString("; ")}")
        }
    }
}

private fun printPlannerTable(report: SimulationReport) {
    println(
        String.format(
            Locale.ROOT,
            "%-24s %-20s %8s %6s %8s",
            "planner",
            "scenario",
            "reward",
            "steps",
            "gap",
        ),
    )
    println("-".repeat(70))
    for (row in report.rows) {
        val gap = row.optimalityGap?.let { String.format(Locale.ROOT, "%.3f", it) } ?: "n/a"
        println(
            String.format(
                Locale.ROOT,
                "%-24s %-20s %8.3f %6d %8s",
                row.planner,
                row.scenario,
                row.totalReward,
                row.steps,
                gap,
            ),
        )
    }
    println("-".repeat(70))
    println(String.format(Locale.ROOT, "%-24s %s", "best", report.best() ?: "none"))
}

private fun usage(): Int {
    System.err.println("usage: laix-bench [--suite NAME]... [--planners] [--live] [--json] [--list] [--fail-under N]")
    return 2
}

/** The suite names the CLI accepts. */
val BENCH_SUITE_NAMES: List<String> = suiteNames()
