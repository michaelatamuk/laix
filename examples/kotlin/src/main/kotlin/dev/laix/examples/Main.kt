package dev.laix.examples

import kotlin.system.exitProcess

/**
 * Run one example, or list them.
 *
 * `laix-examples --list` prints the paths; `--all` runs everything; a path
 * substring runs the matching examples.
 */
fun main(args: Array<String>) {
    exitProcess(run(args.toList()))
}

fun run(args: List<String>): Int {
    when {
        args.isEmpty() || args[0] == "--list" -> {
            for (example in examples) {
                println("%-52s %s".format(example.path, example.description))
            }
            return 0
        }
        args[0] == "--all" -> {
            examples.forEach { execute(it) }
            return 0
        }
        else -> {
            val needle = args[0]
            val matches = examples.filter { it.path.contains(needle) }
            if (matches.isEmpty()) {
                System.err.println("laix-examples: no example matches '$needle'")
                return 2
            }
            matches.forEach { execute(it) }
            return 0
        }
    }
}

private fun execute(example: Example) {
    println("== ${example.path}")
    println(example.body())
}
