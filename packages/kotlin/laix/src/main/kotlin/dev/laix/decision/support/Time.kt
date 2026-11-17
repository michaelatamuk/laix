package dev.laix.decision.support

import java.time.Instant
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.util.UUID

/** Stable, prefix-readable identifiers. */
fun newId(prefix: String): String =
    "$prefix-${UUID.randomUUID().toString().replace("-", "").take(10).uppercase()}"

private val ISO_SECONDS: DateTimeFormatter =
    DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssxxx")

private val ISO_NAIVE_SECONDS: DateTimeFormatter =
    DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")

private val ISO_OFFSET: DateTimeFormatter = DateTimeFormatter.ofPattern("xxx")

/** UTC clock and ISO-8601 helper matching the Python records. */
fun utcNow(): OffsetDateTime = OffsetDateTime.now(ZoneOffset.UTC)

fun iso(value: OffsetDateTime? = null): String =
    (value ?: utcNow())
        .withOffsetSameInstant(ZoneOffset.UTC)
        .truncatedTo(ChronoUnit.SECONDS)
        .format(ISO_SECONDS)

/**
 * Format an instant the way Python's `datetime.isoformat()` does: the moment's
 * own offset, and microseconds only when they are non-zero.
 */
fun isoFull(value: OffsetDateTime? = null): String {
    val moment = value ?: utcNow()
    val base = moment.format(ISO_NAIVE_SECONDS)
    val micros = moment.nano / 1_000
    val fraction = if (micros == 0) {
        ""
    } else {
        String.format(java.util.Locale.ROOT, ".%06d", micros)
    }
    return base + fraction + moment.format(ISO_OFFSET)
}

/** Parse an ISO-8601 instant, accepting naive values as UTC. */
fun parseIso(value: String?): OffsetDateTime? {
    if (value.isNullOrBlank()) return null
    val parsed = runCatching { OffsetDateTime.parse(value) }.getOrNull()
        ?: runCatching { LocalDateTime.parse(value).atOffset(ZoneOffset.UTC) }.getOrNull()
        ?: runCatching { Instant.parse(value).atOffset(ZoneOffset.UTC) }.getOrNull()
    // Python's parse_iso normalises every instant to UTC.
    return parsed?.withOffsetSameInstant(ZoneOffset.UTC)
}

/**
 * Parse an instant like Python's `datetime.fromisoformat`, which keeps the
 * offset written in the value.
 */
fun parseIsoLocal(value: String?): OffsetDateTime? {
    if (value.isNullOrBlank()) return null
    return runCatching { OffsetDateTime.parse(value) }.getOrNull()
        ?: runCatching { LocalDateTime.parse(value).atOffset(ZoneOffset.UTC) }.getOrNull()
        ?: runCatching { Instant.parse(value).atOffset(ZoneOffset.UTC) }.getOrNull()
}
