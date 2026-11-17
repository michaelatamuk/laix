package dev.laix.decision.appkit

import dev.laix.decision.appkit.audit.Proposal
import dev.laix.decision.appkit.audit.approve
import dev.laix.decision.appkit.audit.apply
import dev.laix.decision.appkit.audit.reject
import dev.laix.decision.appkit.audit.undo
import dev.laix.decision.appkit.commitments.InMemoryCommitmentResolver
import dev.laix.decision.appkit.commitments.resolveCommitmentGraph
import dev.laix.decision.appkit.state.ExperienceState
import dev.laix.decision.appkit.state.FileStateStore
import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.commitments.CommitmentRef
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class AuditAndResolversTest {
    @Test
    fun `proposals follow their lifecycle`() {
        val proposal = Proposal(id = "p-1", title = "Pay", summary = "Pay the invoice")

        val approved = approve(proposal, by = "lead", at = "2026-11-01T10:00:00+00:00")
        assertEquals("approved", approved.status)
        assertEquals("lead", approved.approvedBy)

        val applied = apply(approved, at = "2026-11-01T10:01:00+00:00")
        assertEquals("applied", applied.status)

        val undone = undo(applied, at = "2026-11-01T10:02:00+00:00")
        assertEquals("undone", undone.status)

        assertFailsWith<IllegalArgumentException> { approve(approved, by = "lead") }
        assertFailsWith<IllegalArgumentException> { apply(proposal) }
        assertFailsWith<IllegalArgumentException> { undo(approved) }
        assertEquals("rejected", reject(proposal, by = "lead").status)
    }

    @Test
    fun `resolvers build the graph from external refs`() {
        val supplier = CommitmentRef(owner = "supplier", ledger = "supplier", id = "ship")
        val local = CommitmentLedger(
            listOf(
                Commitment(
                    id = "deliver",
                    subject = "deliver",
                    externalDependsOn = listOf(supplier),
                ),
            ),
        )
        val resolver = InMemoryCommitmentResolver(
            listOf(
                Commitment(
                    id = "ship",
                    subject = "ship",
                    owner = "supplier",
                    ledger = "supplier",
                    status = "done",
                    source = "verified",
                    verifiedAt = "2026-11-01T09:00:00+00:00",
                ),
            ),
        )

        val graph = resolveCommitmentGraph(local, resolver)

        assertEquals(2, graph.commitments.size)
        assertTrue(graph.missingRefs().isEmpty())
        assertEquals("ship", graph.get(supplier)?.id)
    }

    @Test
    fun `an unresolved ref is reported as missing`() {
        val local = CommitmentLedger(
            listOf(
                Commitment(
                    id = "deliver",
                    subject = "deliver",
                    externalDependsOn = listOf(
                        CommitmentRef(owner = "supplier", id = "ship"),
                    ),
                ),
            ),
        )

        val graph = resolveCommitmentGraph(local, InMemoryCommitmentResolver())

        assertEquals(1, graph.missingRefs().size)
    }

    @Test
    fun `the async resolver builds the same graph`() = kotlinx.coroutines.runBlocking {
        val ref = CommitmentRef(owner = "supplier", ledger = "supplier", id = "ship")
        val local = CommitmentLedger(
            listOf(Commitment(id = "deliver", subject = "deliver", externalDependsOn = listOf(ref))),
        )
        val resolver = object : dev.laix.decision.appkit.commitments.AsyncCommitmentResolver {
            override suspend fun resolve(refs: List<CommitmentRef>): List<Commitment> =
                listOf(
                    Commitment(
                        id = "ship",
                        subject = "ship",
                        owner = "supplier",
                        ledger = "supplier",
                        status = "done",
                    ),
                )
        }

        val graph = dev.laix.decision.appkit.commitments.resolveCommitmentGraphAsync(local, resolver)

        assertEquals(2, graph.commitments.size)
        assertEquals("ship", graph.get(ref)?.id)
    }

    @Test
    fun `the file state store round-trips snapshots`(@TempDir directory: Path) {
        val store = FileStateStore(directory.resolve("states"))
        val state = ExperienceState(subject = "demo")
        state.advance("act")

        store.save("task/1", state)
        val file = directory.resolve("states").resolve("task_1.json")
        assertTrue(Files.exists(file))

        val restored = store.load("task/1")
        assertEquals("demo", restored?.subject)
        assertEquals("act", restored?.phase)

        store.delete("task/1")
        assertEquals(null, store.load("task/1"))
        assertTrue(!Files.exists(file))
    }
}
