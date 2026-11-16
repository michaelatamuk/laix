package dev.laix.decision.commitments

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
