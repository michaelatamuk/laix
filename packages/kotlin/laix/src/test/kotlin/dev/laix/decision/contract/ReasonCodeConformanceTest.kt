package dev.laix.decision.contract

import dev.laix.decision.contracts.SCHEMA_VERSION
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ReasonCodeConformanceTest {
    private val contract: Path = findContract()

    private fun findContract(): Path {
        var dir: Path? = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize()
        while (dir != null) {
            val candidate = dir.resolve("contracts").resolve("reason-codes.v1.json")
            if (Files.exists(candidate)) return candidate
            val nested = dir.resolve("packages").resolve("contracts").resolve("reason-codes.v1.json")
            if (Files.exists(nested)) return nested
            dir = dir.parent
        }
        error("could not find reason-codes.v1.json above ${System.getProperty("user.dir")}")
    }

    @Test
    fun `registry matches the shared contract`() {
        assertTrue(Files.exists(contract), "missing contract at $contract")
        val payload = Json.parseToJsonElement(Files.readString(contract)).jsonObject
        val groups = payload.getValue("groups").jsonObject

        assertEquals(payload.getValue("version").jsonPrimitive.content, ReasonCodes.VERSION)
        assertEquals(ReasonCodes.GROUPS.keys, groups.keys)
        assertEquals(
            payload.getValue("schema_version").jsonPrimitive.content,
            SCHEMA_VERSION,
        )
        assertEquals(payload.getValue("note").jsonPrimitive.content, ReasonCodes.NOTE)

        for ((name, expected) in groups) {
            val actual = ReasonCodes.GROUPS.getValue(name)
            assertEquals(
                expected.jsonArray.map { it.jsonPrimitive.content },
                actual,
                "group $name",
            )
        }

        val codes = payload.getValue("codes").jsonArray.map { it.jsonPrimitive.content }
        assertEquals(codes, ReasonCodes.CODES)
        assertEquals(codes.sorted(), ReasonCodes.CODES)
    }

    @Test
    fun `registry carries the published flags`() {
        val payload = Json.parseToJsonElement(Files.readString(contract)).jsonObject
        val registry = ReasonCodes.registry()

        assertEquals(payload.getValue("extensible").jsonPrimitive.content.toBoolean(), registry["extensible"])
        assertEquals(ReasonCodes.VERSION, registry["version"])
        assertEquals(SCHEMA_VERSION, registry["schema_version"])
        assertEquals(ReasonCodes.NOTE, registry["note"])
        assertEquals(ReasonCodes.CODES, registry["codes"])
    }
}
