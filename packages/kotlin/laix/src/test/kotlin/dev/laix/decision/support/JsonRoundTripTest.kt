package dev.laix.decision.support

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef
import dev.laix.decision.commitments.FileCommitmentStore
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.ScoreBreakdown
import dev.laix.decision.contracts.Verb
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class JsonRoundTripTest {
    @Test
    fun `decisions round-trip with the published snake_case keys`() {
        val decision = Decision(
            verb = Verb.ASK,
            confidence = 0.82,
            reasonCode = "policy_rule",
            rationale = "ask first",
            decisionId = "DEC-1",
            actionId = "a-1",
            evidence = listOf(EvidenceRef(id = "e-1", kind = "document", quote = "quote", source = "mail")),
            breakdown = ScoreBreakdown(severity = 45.0, due = 20.0, confidence = 16.0, total = 81.0),
            intent = Intent("ask_user", mapOf("question" to "which one?")),
            alternatives = listOf(mapOf("action_id" to "a-2", "utility" to 0.3)),
            constraintsApplied = listOf("approval:human-required"),
            attributes = mapOf("urgency" to 0.5),
        )

        val text = decision.toJson()
        assertTrue(text.contains("\"reason_code\":\"policy_rule\""))
        assertTrue(text.contains("\"schema_version\""))
        assertEquals(decision.toMap(), Decision.fromJson(text).toMap())
    }

    @Test
    fun `commitments and refs round-trip`() {
        val ref = CommitmentRef(owner = "supplier", ledger = "supplier", id = "ship")
        assertEquals(ref, CommitmentRef.fromJson(ref.toJson()))

        val commitment = Commitment(
            id = "deliver",
            subject = "deliver",
            due = "2026-11-02T10:00:00+00:00",
            dependsOn = listOf("pack"),
            payload = mapOf("lines" to listOf(1L, 2L)),
            externalDependsOn = listOf(ref),
        )
        assertEquals(commitment, Commitment.fromJson(commitment.toJson()))
    }

    @Test
    fun `ledgers and graphs round-trip`() {
        val graph = CommitmentGraph(
            CommitmentLedger(
                listOf(Commitment(id = "a", subject = "a"), Commitment(id = "b", subject = "b", dependsOn = listOf("a"))),
            ),
            listOf(Commitment(id = "c", subject = "c", owner = "other", ledger = "other")),
        )

        val restored = CommitmentGraph.fromJson(graph.toJson())

        assertEquals(graph.toMap(), restored.toMap())
        assertEquals(listOf("a", "b", "c"), restored.commitments.map { it.id })
    }

    @Test
    fun `the file store writes and reads one file per ledger`(@TempDir directory: Path) {
        val store = FileCommitmentStore(directory.resolve("ledgers"))
        val ledger = CommitmentLedger(listOf(Commitment(id = "a", subject = "a")))
        store.save("task/1", ledger)
        val file = directory.resolve("ledgers").resolve("task_1.json")

        assertTrue(Files.exists(file))
        assertTrue(Files.readString(file).contains("\n"))
        assertEquals(ledger.toMap(), store.load("task/1")?.toMap())

        store.delete("task/1")
        assertNull(store.load("task/1"))
        assertTrue(!Files.exists(file))
    }

    @Test
    fun `plain values serialize and parse`() {
        val value = mapOf("a" to 1L, "b" to listOf(true, null, "x"), "c" to 1.5)

        assertEquals(value, parseJson(value.toJson()))
    }
}
