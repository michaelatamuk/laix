package dev.laix.decision.support

import java.math.BigDecimal
import java.math.RoundingMode

fun clamp(value: Double, low: Double = 0.0, high: Double = 1.0): Double =
    maxOf(low, minOf(high, value))

/**
 * Round one value the way Python's `round(value, places)` does.
 *
 * Python rounds the exact binary double, not its shortest decimal rendering,
 * so this uses `BigDecimal(value)` rather than `BigDecimal.valueOf(value)`.
 */
fun round(value: Double, places: Int): Double {
    if (!value.isFinite()) return value
    if (value == 0.0) return value
    val rounded = BigDecimal(value).setScale(places, RoundingMode.HALF_EVEN).toDouble()
    // BigDecimal has no signed zero; Python's round keeps the sign.
    return if (rounded == 0.0) Math.copySign(0.0, value) else rounded
}

fun round6(value: Double): Double = round(value, 6)

/** Python truthiness: every non-empty string, non-zero number and non-empty collection is true. */
fun truthy(value: Any?): Boolean =
    when (value) {
        is String -> value.isNotEmpty()
        is Boolean -> value
        is Number -> value.toDouble() != 0.0
        is Collection<*> -> value.isNotEmpty()
        is Map<*, *> -> value.isNotEmpty()
        is Array<*> -> value.isNotEmpty()
        null -> false
        else -> true
    }

/**
 * The planner-specific truthiness used by the Python policies for constraint
 * values. It differs from Python `bool()` for strings: only an explicit set of
 * tokens counts as true.
 */
fun policyTruthy(value: Any?): Boolean =
    when (value) {
        is String -> value.trim().lowercase() in
            setOf("1", "true", "yes", "required", "always", "blocked", "on")
        else -> truthy(value)
    }

/** Coerce a value the way Python's `float(value)` does, or `null` when it cannot. */
fun asNumber(value: Any?): Double? =
    when (value) {
        is Number -> value.toDouble()
        is String -> value.trim().toDoubleOrNull()
        else -> null
    }

fun asInt(value: Any?): Int? = asNumber(value)?.toInt()

/**
 * Python equality.
 *
 * Python treats `1`, `1.0` and `True` as equal, while Kotlin's `==` compares
 * the runtime types. Rules and duck-typed payloads are compared with this
 * helper so a JSON number matches an int or a float the same way.
 */
fun pythonEquals(left: Any?, right: Any?): Boolean {
    fun numeric(value: Any?): Double? = when (value) {
        is Boolean -> if (value) 1.0 else 0.0
        is Number -> value.toDouble()
        else -> null
    }
    if (left is String || right is String) return left == right
    val leftNumber = numeric(left)
    val rightNumber = numeric(right)
    if (leftNumber != null && rightNumber != null) return leftNumber == rightNumber
    return left == right
}

/** Python's `in` operator over strings, maps, sets and other iterables. */
fun pythonIn(container: Any?, item: Any?): Boolean =
    when (container) {
        null -> false
        is String -> item is String && container.contains(item)
        is Map<*, *> -> container.keys.any { pythonEquals(it, item) }
        is Iterable<*> -> container.any { pythonEquals(it, item) }
        is Array<*> -> container.any { pythonEquals(it, item) }
        else -> false
    }

/**
 * Approximate Python's `repr` for JSON-shaped values.
 *
 * The planner records a couple of free-form notes with `str(value)`; Python
 * renders dictionaries and lists with single quotes, so Kotlin does too.
 */
fun pythonRepr(value: Any?): String =
    when (value) {
        null -> "None"
        is Boolean -> if (value) "True" else "False"
        is String -> "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
        is Double -> pythonFloatRepr(value)
        is Float -> pythonFloatRepr(value.toDouble())
        is Map<*, *> -> value.entries.joinToString(", ", "{", "}") {
            "${pythonRepr(it.key.toString())}: ${pythonRepr(it.value)}"
        }
        is Iterable<*> -> value.joinToString(", ", "[", "]") { pythonRepr(it) }
        is Array<*> -> value.joinToString(", ", "[", "]") { pythonRepr(it) }
        else -> value.toString()
    }

/** Python's `repr(float)` and `json.dumps` float rendering. */
fun pythonFloatRepr(value: Double): String {
    if (value.isNaN()) return "NaN"
    if (value == Double.POSITIVE_INFINITY) return "Infinity"
    if (value == Double.NEGATIVE_INFINITY) return "-Infinity"
    if (value == 0.0) return if (1.0 / value < 0) "-0.0" else "0.0"
    val decimal = BigDecimal.valueOf(value).stripTrailingZeros()
    val sign = if (decimal.signum() < 0) "-" else ""
    val digits = decimal.unscaledValue().abs().toString()
    val exponent = digits.length - 1 - decimal.scale()
    if (exponent < -4 || exponent >= 16) {
        val mantissa = if (digits.length == 1) digits else "${digits[0]}.${digits.substring(1)}"
        val expSign = if (exponent < 0) "-" else "+"
        return sign + mantissa + "e" + expSign + kotlin.math.abs(exponent).toString().padStart(2, '0')
    }
    return if (exponent >= 0) {
        val whole = digits.padEnd(exponent + 1, '0')
        val fraction = whole.substring(exponent + 1).ifEmpty { "0" }
        "$sign${whole.substring(0, exponent + 1)}.$fraction"
    } else {
        val fraction = "0".repeat(-exponent - 1) + digits
        "${sign}0.$fraction"
    }
}

/**
 * Python's `json.dumps(string)` with `ensure_ascii=True`.
 *
 * Non-ASCII characters are escaped as `\uXXXX`, so a decision-record hash is
 * stable across languages and platforms.
 */
fun pythonJsonString(value: String): String {
    val builder = StringBuilder(value.length + 2)
    builder.append('"')
    for (character in value) {
        when {
            character == '"' -> builder.append("\\\"")
            character == '\\' -> builder.append("\\\\")
            character == '\b' -> builder.append("\\b")
            character == '\u000c' -> builder.append("\\f")
            character == '\n' -> builder.append("\\n")
            character == '\r' -> builder.append("\\r")
            character == '\t' -> builder.append("\\t")
            character < ' ' || character > '~' ->
                builder.append("\\u").append(character.code.toString(16).padStart(4, '0'))
            else -> builder.append(character)
        }
    }
    builder.append('"')
    return builder.toString()
}

fun confidenceBand(value: Double): String =
    when {
        value >= 0.8 -> "high"
        value >= 0.55 -> "medium"
        else -> "low"
    }
