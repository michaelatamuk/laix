package dev.laix.decision.support

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

/** UTC clock and ISO-8601 helper matching the Python records. */
fun utcNow(): OffsetDateTime = OffsetDateTime.now(ZoneOffset.UTC)

fun iso(value: OffsetDateTime? = null): String =
    (value ?: utcNow())
        .withOffsetSameInstant(ZoneOffset.UTC)
        .truncatedTo(ChronoUnit.SECONDS)
        .format(ISO_SECONDS)
