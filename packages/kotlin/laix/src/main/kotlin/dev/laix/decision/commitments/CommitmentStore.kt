package dev.laix.decision.commitments

import dev.laix.decision.support.toJson
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption

/** Save, load and delete one commitment ledger. */
interface CommitmentStore {
    fun save(key: String, ledger: CommitmentLedger)

    fun load(key: String): CommitmentLedger?

    fun delete(key: String)
}

/** A process-local store, useful in tests. */
class InMemoryCommitmentStore : CommitmentStore {
    private val items = linkedMapOf<String, Map<String, Any?>>()

    override fun save(key: String, ledger: CommitmentLedger) {
        items[key] = ledger.toMap()
    }

    override fun load(key: String): CommitmentLedger? {
        val payload = items[key] ?: return null
        return CommitmentLedger.fromMap(payload)
    }

    override fun delete(key: String) {
        items.remove(key)
    }
}

/** One JSON file per ledger, under a host-owned directory. */
class FileCommitmentStore(val directory: Path) : CommitmentStore {
    init {
        Files.createDirectories(directory)
    }

    private fun path(key: String): Path {
        val safe = key.map { if (it in "/\\:*?\"<>|") '_' else it }.joinToString("")
        return directory.resolve("$safe.json")
    }

    override fun save(key: String, ledger: CommitmentLedger) {
        val target = path(key)
        val temporary = target.resolveSibling("${target.fileName}.tmp")
        Files.writeString(temporary, ledger.toJson(pretty = true), Charsets.UTF_8)
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

    override fun load(key: String): CommitmentLedger? {
        val target = path(key)
        if (!Files.exists(target)) return null
        return CommitmentLedger.fromJson(Files.readString(target))
    }

    override fun delete(key: String) {
        Files.deleteIfExists(path(key))
    }
}
