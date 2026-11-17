package dev.laix.decision.support

import java.math.BigDecimal
import java.math.RoundingMode

fun clamp(value: Double, low: Double = 0.0, high: Double = 1.0): Double =
    maxOf(low, minOf(high, value))

fun round6(value: Double): Double =
    BigDecimal.valueOf(value).setScale(6, RoundingMode.HALF_EVEN).toDouble()

fun round(value: Double, places: Int): Double =
    BigDecimal.valueOf(value).setScale(places, RoundingMode.HALF_EVEN).toDouble()

fun truthy(value: Any?): Boolean =
    when (value) {
        is String -> value.trim().lowercase() in
            setOf("1", "true", "yes", "required", "always", "blocked", "on")
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        is Collection<*> -> value.isNotEmpty()
        is Map<*, *> -> value.isNotEmpty()
        null -> false
        else -> true
    }

fun confidenceBand(value: Double): String =
    when {
        value >= 0.8 -> "high"
        value >= 0.55 -> "medium"
        else -> "low"
    }
