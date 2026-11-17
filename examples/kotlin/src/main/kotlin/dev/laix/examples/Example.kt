package dev.laix.examples

/** One runnable example: a stable path, a one-line description and its body. */
data class Example(
    val path: String,
    val description: String,
    val body: () -> String,
)
