package dev.laix.decision.support

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull

/** Convert plain maps, lists and scalars into JSON. */
fun toJsonElement(value: Any?): JsonElement =
    when (value) {
        null -> JsonNull
        is JsonElement -> value
        is Boolean -> JsonPrimitive(value)
        is Number -> JsonPrimitive(value)
        is String -> JsonPrimitive(value)
        is Map<*, *> -> JsonObject(
            value.entries.associate { (key, item) -> key.toString() to toJsonElement(item) },
        )
        is Iterable<*> -> JsonArray(value.map { toJsonElement(it) })
        is Array<*> -> JsonArray(value.map { toJsonElement(it) })
        else -> JsonPrimitive(value.toString())
    }

/** Convert JSON back to the plain maps, lists and scalars the public API accepts. */
fun JsonElement.toPlain(): Any? =
    when (this) {
        is JsonObject -> entries.associate { (key, value) -> key to value.toPlain() }
        is JsonArray -> map { it.toPlain() }
        is JsonPrimitive -> when {
            booleanOrNull != null -> booleanOrNull
            isString -> content
            content == "null" -> null
            else -> content.toLongOrNull() ?: content.toDoubleOrNull() ?: content
        }
    }

/** Serialize a contract value to JSON. Keys stay snake_case, as in the Python and TypeScript packages. */
@OptIn(kotlinx.serialization.ExperimentalSerializationApi::class)
fun Any?.toJson(pretty: Boolean = false): String {
    val json = if (pretty) {
        Json { prettyPrint = true; prettyPrintIndent = "  " }
    } else {
        Json
    }
    return json.encodeToString(JsonElement.serializer(), toJsonElement(this))
}

fun parseJson(text: String): Any? = Json.parseToJsonElement(text).toPlain()

fun parseJsonObject(text: String): Map<String, Any?> {
    val element = Json.parseToJsonElement(text)
    require(element is JsonObject) { "expected a JSON object" }
    @Suppress("UNCHECKED_CAST")
    return element.toPlain() as Map<String, Any?>
}
