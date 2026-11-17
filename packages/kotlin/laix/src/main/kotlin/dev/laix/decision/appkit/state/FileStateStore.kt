package dev.laix.decision.appkit.state

import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption

/**
 * One JSON file per experience state, under a host-owned directory.
 *
 * The format is `ExperienceState.snapshot()`: plain JSON the host can inspect,
 * back up or migrate without importing LAIX.
 */
class FileStateStore(val directory: Path) : StateStore {
    init {
        Files.createDirectories(directory)
    }

    private fun path(key: String): Path {
        val safe = key.map { if (it in "/\\:*?\"<>|") '_' else it }.joinToString("")
        return directory.resolve("$safe.json")
    }

    override fun save(key: String, state: ExperienceState) {
        val target = path(key)
        val temporary = target.resolveSibling("${target.fileName}.tmp")
        Files.writeString(temporary, state.snapshot().toJson(pretty = true), Charsets.UTF_8)
        try {
            Files.move(
                temporary,
                target,
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE,
            )
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING)
        }
    }

    override fun load(key: String): ExperienceState? {
        val target = path(key)
        if (!Files.exists(target)) return null
        return ExperienceState.fromSnapshot(parseJsonObject(Files.readString(target)))
    }

    override fun delete(key: String) {
        Files.deleteIfExists(path(key))
    }
}
