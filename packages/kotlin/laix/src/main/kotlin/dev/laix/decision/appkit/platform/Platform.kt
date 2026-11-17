package dev.laix.decision.appkit.platform

import dev.laix.decision.support.iso

val CAPABILITY_LEVELS: List<String> = listOf("fast", "balanced", "deep")

/** A capability level, not a model name. */
data class Capability(
    val level: String,
    val modalities: List<String> = emptyList(),
    val maxLatencyMs: Int? = null,
    val maxCost: Double? = null,
) {
    init {
        require(level in CAPABILITY_LEVELS) { "unknown capability level: '$level'" }
    }
}

/** One named skill call the app asks the platform to run. */
data class SkillCall(
    val capability: String,
    val args: Map<String, Any?> = emptyMap(),
    val traceId: String = "",
)

/** The approval a platform is asked to obtain. */
data class ApprovalRequest(
    val decisionId: String,
    val actionName: String,
    val rationale: String = "",
    val risk: Double = 0.0,
    val reversible: Boolean = true,
    val evidence: List<String> = emptyList(),
)

/** What the platform or approver decided about a request. */
data class ApprovalDecision(
    val approved: Boolean,
    val by: String = "",
    val at: String = "",
    val note: String = "",
)

/** One platform event streamed back for a trace. */
data class PlatformEvent(
    val traceId: String,
    val kind: String,
    val at: String = "",
    val payload: Map<String, Any?> = emptyMap(),
)

/** The south interface: what LAIX needs from the platform underneath it. */
interface Platform {
    fun runSkill(call: SkillCall): Any?

    fun cancel(runId: String, reason: String = ""): Boolean

    fun requestApproval(request: ApprovalRequest): ApprovalDecision

    fun readState(key: String): Any?

    fun writeState(key: String, value: Any?)

    fun events(traceId: String): List<PlatformEvent>

    fun capability(level: String): Capability
}

/** A small platform for tests and local runs. */
class InMemoryPlatform(
    private val approver: ((ApprovalRequest) -> ApprovalDecision)? = null,
) : Platform {
    private val skills = LinkedHashMap<String, (SkillCall) -> Any?>()
    private val state = LinkedHashMap<String, Any?>()
    private val events = mutableListOf<PlatformEvent>()
    private val capabilities = mapOf(
        "fast" to Capability("fast", listOf("text"), 200, 0.001),
        "balanced" to Capability("balanced", listOf("text", "image"), 1500, 0.02),
        "deep" to Capability(
            "deep",
            listOf("text", "image", "audio", "video"),
            15000,
            0.2,
        ),
    )

    fun register(capability: String, handler: (SkillCall) -> Any?) {
        skills[capability] = handler
    }

    override fun runSkill(call: SkillCall): Any? {
        val handler = skills[call.capability]
            ?: throw NoSuchElementException("no skill registered for '${call.capability}'")
        events += PlatformEvent(
            call.traceId,
            "skill.started",
            iso(),
            mapOf("capability" to call.capability),
        )
        val result = handler(call)
        events += PlatformEvent(
            call.traceId,
            "skill.finished",
            iso(),
            mapOf("capability" to call.capability),
        )
        return result
    }

    override fun cancel(runId: String, reason: String): Boolean {
        events += PlatformEvent(runId, "skill.cancelled", iso(), mapOf("reason" to reason))
        return true
    }

    override fun requestApproval(request: ApprovalRequest): ApprovalDecision {
        val decision = approver?.invoke(request) ?: ApprovalDecision(
            approved = false,
            by = "",
            at = iso(),
            note = "no approver configured",
        )
        events += PlatformEvent(
            request.decisionId,
            "approval.decided",
            iso(),
            mapOf("approved" to decision.approved, "by" to decision.by),
        )
        return decision
    }

    override fun readState(key: String): Any? = state[key]

    override fun writeState(key: String, value: Any?) {
        state[key] = value
    }

    override fun events(traceId: String): List<PlatformEvent> =
        events.filter { it.traceId == traceId }

    override fun capability(level: String): Capability =
        capabilities[level] ?: throw IllegalArgumentException("unknown capability level: '$level'")
}
