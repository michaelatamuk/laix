package dev.laix.examples

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class ExamplesTest {
    @Test
    fun `every example runs and prints something`() {
        for (example in examples) {
            val output = example.body()
            assertTrue(output.isNotBlank(), "example ${example.path} printed nothing")
        }
    }

    @Test
    fun `paths are unique and named after their folder`() {
        val paths = examples.map { it.path }
        assertEquals(paths.size, paths.toSet().size)
        assertTrue(paths.all { it.startsWith("decision/") || it.startsWith("appkit/") })
    }

    @Test
    fun `every example has a description`() {
        assertTrue(examples.all { it.description.isNotBlank() })
    }
}
