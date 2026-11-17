package dev.laix.decision.signals

import java.time.OffsetDateTime

/** Parse an ISO-8601 instant, accepting naive values as UTC. */
@Deprecated("Use dev.laix.decision.support.parseIso")
fun parseIso(value: String?): OffsetDateTime? = dev.laix.decision.support.parseIso(value)

/** True inside the window, inclusive on both ends. Bad input is never quiet. */
fun isQuiet(now: OffsetDateTime, quietHours: Any?): Boolean {
    val window = QuietHours.parse(quietHours) ?: return false
    val start = minutes(window.start) ?: return false
    val end = minutes(window.end) ?: return false
    val minute = now.hour * 60 + now.minute
    return if (start <= end) {
        start <= minute && minute <= end
    } else {
        minute >= start || minute <= end
    }
}

private fun minutes(value: String): Int? =
    runCatching {
        val (hour, minute) = value.split(':', limit = 2)
        hour.trim().toInt() * 60 + minute.trim().toInt()
    }.getOrNull()

/** Hours from `now` to `whenIso`. Negative means overdue. `null` when unparsable. */
fun hoursUntil(now: OffsetDateTime, whenIso: String?): Double? {
    val whenValue = dev.laix.decision.support.parseIso(whenIso) ?: return null
    return (whenValue.toInstant().toEpochMilli() - now.toInstant().toEpochMilli()) / 3_600_000.0
}
