package dev.laix.decision.support

import java.math.BigDecimal
import java.math.RoundingMode

fun clamp(value: Double, low: Double = 0.0, high: Double = 1.0): Double =
    maxOf(low, minOf(high, value))

fun round6(value: Double): Double =
    BigDecimal.valueOf(value).setScale(6, RoundingMode.HALF_EVEN).toDouble()

fun truthy(value: Any?): Boolean =
    when (value) {
        is String -> value.trim().lowercase() in
            setOf("1", "true", "yes", "required", "always", "blocked", "on")
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        null -> false
        else -> true
    }
