package dev.laix.decision.outcomes

import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class FileOutcomeStoreTest {
    @Test
    fun `reads an empty store`(@TempDir directory: Path) {
        val store = FileOutcomeStore(directory)

        assertEquals(emptyList(), store.all())
        assertTrue(!Files.exists(store.path))
    }

    @Test
    fun `persists every record and reloads`(@TempDir directory: Path) {
        val store = FileOutcomeStore(directory)
        store.add(
            Outcome(
                id = "OUT-1",
                decisionId = "DEC-1",
                metric = "precision",
                before = 0.2,
                after = 0.6,
                delta = 0.4,
                label = "helped",
                attributed = true,
            ),
        )
        store.record(
            decisionId = "DEC-2",
            metric = "time",
            before = 10.0,
            after = 4.0,
            direction = "lower-better",
            attributed = true,
        )

        assertTrue(Files.exists(store.path))
        assertTrue(Files.readString(store.path).contains("\n"))

        val reloaded = FileOutcomeStore(directory)
        assertEquals(2, reloaded.all().size)
        assertEquals(listOf("DEC-1"), reloaded.forDecision("DEC-1").map { it.decisionId })
        assertEquals(2, reloaded.summary()["attributed"])
        assertEquals(2, reloaded.summary()["helped"])
    }
}
