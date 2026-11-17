package dev.laix.decision.appkit

import dev.laix.decision.appkit.platform.ApprovalDecision
import dev.laix.decision.appkit.platform.ApprovalRequest
import dev.laix.decision.appkit.platform.Capability
import dev.laix.decision.appkit.platform.InMemoryPlatform
import dev.laix.decision.appkit.platform.SkillCall
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class PlatformTest {
    @Test
    fun `skills run and emit events`() {
        val platform = InMemoryPlatform()
        platform.register("lookup") { call ->
            mapOf("echo" to call.args["q"])
        }

        val result = platform.runSkill(
            SkillCall("lookup", mapOf("q" to "hello"), traceId = "TRC-1"),
        )

        assertEquals(mapOf("echo" to "hello"), result)
        val events = platform.events("TRC-1")
        assertEquals(listOf("skill.started", "skill.finished"), events.map { it.kind })
    }

    @Test
    fun `unknown skills fail`() {
        assertFailsWith<NoSuchElementException> {
            InMemoryPlatform().runSkill(SkillCall("missing"))
        }
    }

    @Test
    fun `approval uses the configured approver`() {
        val platform = InMemoryPlatform { request ->
            ApprovalDecision(approved = true, by = "lead", at = "now", note = request.rationale)
        }

        val decision = platform.requestApproval(
            ApprovalRequest("DEC-1", "pay", rationale = "invoice"),
        )

        assertEquals(true, decision.approved)
        assertEquals("lead", decision.by)
        assertEquals("invoice", decision.note)
        assertEquals("approval.decided", platform.events("DEC-1").single().kind)
    }

    @Test
    fun `approval defaults to no approver`() {
        val decision = InMemoryPlatform().requestApproval(
            ApprovalRequest("DEC-1", "pay"),
        )

        assertEquals(false, decision.approved)
        assertTrue(decision.note.contains("no approver"))
    }

    @Test
    fun `state and cancellation work`() {
        val platform = InMemoryPlatform()

        assertEquals(null, platform.readState("k"))
        platform.writeState("k", mapOf("v" to 1))
        assertEquals(mapOf("v" to 1), platform.readState("k"))
        assertEquals(true, platform.cancel("run-1", "stop"))
        assertEquals("skill.cancelled", platform.events("run-1").single().kind)
    }

    @Test
    fun `capabilities expose levels`() {
        val platform = InMemoryPlatform()

        assertEquals(listOf("text"), platform.capability("fast").modalities)
        assertEquals(15000, platform.capability("deep").maxLatencyMs)
        assertFailsWith<IllegalArgumentException> { platform.capability("super") }
        assertFailsWith<IllegalArgumentException> { Capability("super") }
        assertNotNull(platform.capability("balanced").maxCost)
    }
}
