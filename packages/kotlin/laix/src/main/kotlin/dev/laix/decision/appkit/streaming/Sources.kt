package dev.laix.decision.appkit.streaming

import dev.laix.decision.appkit.json.parseRequest
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.support.iso

/** One malformed source frame, kept for inspection. */
data class DeadLetter(
    val raw: String,
    val error: String,
    val at: String = iso(),
)

/** A bounded, callable error sink for NDJSON and SSE sources. */
class DeadLetterQueue(val limit: Int = 100) {
    init {
        require(limit > 0) { "limit must be positive" }
    }

    private val items = mutableListOf<DeadLetter>()

    operator fun invoke(raw: String, exception: Exception) {
        add(raw, exception)
    }

    fun add(raw: String, exception: Exception) {
        items += DeadLetter(raw = raw, error = "${exception::class.simpleName}: ${exception.message}")
        if (items.size > limit) {
            repeat(items.size - limit) { items.removeAt(0) }
        }
    }

    fun all(): List<DeadLetter> = items.toList()

    fun clear() {
        items.clear()
    }

    val size: Int
        get() = items.size

    fun asErrorHandler(): (String, Exception) -> Unit = { raw, error -> add(raw, error) }
}

/** Adapt a synchronous sequence of requests to the stream interface. */
fun fromSync(events: List<DecisionRequest>): List<DecisionRequest> = events

/** Read one request per JSON line. */
fun fromNdjson(
    lines: Iterable<String>,
    onError: ((String, Exception) -> Unit)? = null,
    strict: Boolean = true,
): List<DecisionRequest> {
    val out = mutableListOf<DecisionRequest>()
    for (line in lines) {
        val text = line.trim()
        if (text.isEmpty()) continue
        val request = try {
            parseRequest(
                @Suppress("UNCHECKED_CAST")
                (dev.laix.decision.support.parseJson(text) as? Map<String, Any?>)
                    ?: throw IllegalArgumentException("expected a JSON object"),
            )
        } catch (exception: Exception) {
            onError?.invoke(text, exception)
            if (strict) throw exception
            continue
        }
        out += request
    }
    return out
}

/** Read `data:` frames from a text/event-stream source. */
fun fromSse(
    lines: Iterable<String>,
    onError: ((String, Exception) -> Unit)? = null,
    strict: Boolean = true,
): List<DecisionRequest> {
    val out = mutableListOf<DecisionRequest>()
    var data = mutableListOf<String>()
    fun flush() {
        if (data.isEmpty()) return
        val raw = data.joinToString("\n")
        data = mutableListOf()
        val request = try {
            parseRequest(
                @Suppress("UNCHECKED_CAST")
                (dev.laix.decision.support.parseJson(raw) as? Map<String, Any?>)
                    ?: throw IllegalArgumentException("expected a JSON object"),
            )
        } catch (exception: Exception) {
            onError?.invoke(raw, exception)
            if (strict) throw exception
            return
        }
        out += request
    }
    for (line in lines) {
        if (line.startsWith("data:")) {
            data += line.substring(5).trim()
        } else if (line.isBlank() && data.isNotEmpty()) {
            flush()
        }
    }
    flush()
    return out
}
