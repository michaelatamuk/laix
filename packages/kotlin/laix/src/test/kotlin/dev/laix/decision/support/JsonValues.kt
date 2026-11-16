package dev.laix.decision.support

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import java.nio.file.Files
import java.nio.file.Path

/** Locate a file under the repository's shared `packages/contracts` directory. */
fun contractPath(name: String): Path {
    var dir: Path? = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize()
    while (dir != null) {
        for (candidate in listOf(
            dir.resolve("contracts").resolve(name),
            dir.resolve("packages").resolve("contracts").resolve(name),
        )) {
            if (Files.exists(candidate)) return candidate
        }
        dir = dir.parent
    }
    error("could not find $name above ${System.getProperty("user.dir")}")
}

/** Convert JSON to the plain maps, lists and scalars the public API accepts. */
fun JsonElement.toAny(): Any? =
    when (this) {
        is JsonObject -> entries.associate { (key, value) -> key to value.toAny() }
        is JsonArray -> map { it.toAny() }
        is JsonPrimitive -> when {
            booleanOrNull != null -> booleanOrNull
            isString -> content
            content == "null" -> null
            else -> content.toDoubleOrNull() ?: content
        }
    }
