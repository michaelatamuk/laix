package dev.laix.decision.appkit

import dev.laix.decision.appkit.audit.approve
import dev.laix.decision.appkit.audit.createRecord
import dev.laix.decision.appkit.audit.markExecuted
import dev.laix.decision.appkit.audit.reject
import dev.laix.decision.appkit.audit.undo
import dev.laix.decision.appkit.audit.verify
import dev.laix.decision.appkit.delivery.DeliveryPort
import dev.laix.decision.appkit.delivery.DeliveryReceipt
import dev.laix.decision.appkit.delivery.NullDelivery
import dev.laix.decision.appkit.execution.ApprovalRequired
import dev.laix.decision.appkit.execution.ExecutionBridge
import dev.laix.decision.appkit.execution.RetryPolicy
import dev.laix.decision.appkit.runtime.DecisionRuntime
import dev.laix.decision.appkit.state.ExperienceState
import dev.laix.decision.appkit.state.InMemoryStateStore
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.EvidenceRef
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class AppKitTest {
    private val at = "2026-11-01T10:00:00+00:00"

    private fun situation() = Situation(id = "SIT-1", at = at, subject = "demo")

    private fun options() = listOf(
        ActionOption("a-act", Verb.ACT, "assign_team", expectedBenefit = 0.9),
    )

    private fun decision(actionId: String? = "assign_team", requiresApproval: Boolean = false) =
        Decision(
            verb = Verb.ACT,
            confidence = 0.9,
            reasonCode = "policy_rule",
            rationale = "act",
            decisionId = "DEC-1",
            actionId = actionId,
            requiresApproval = requiresApproval,
        )

    @Test
    fun `the bridge executes registered handlers`() {
        var called = 0
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> ->
                    called++
                    mapOf("assigned" to true)
                },
            ),
        )

        val receipt = bridge.execute(decision(), ActionOption("a", Verb.ACT, "assign_team"), "operator")

        assertEquals("executed", receipt.status)
        assertEquals(mapOf("assigned" to true), receipt.detail)
        assertEquals(1, called)
        assertEquals(receipt, bridge.get(receipt.id))
    }

    @Test
    fun `the bridge requires approval and handles duplicates`() {
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> emptyMap<String, Any?>() },
            ),
        )
        val action = ActionOption("a", Verb.ACT, "assign_team")

        assertFailsWith<ApprovalRequired> {
            bridge.execute(decision(requiresApproval = true), action, "operator")
        }

        val first = bridge.execute(decision(), action, "operator", idempotencyKey = "k-1")
        val duplicate = bridge.execute(decision(), action, "operator", idempotencyKey = "k-1")
        assertEquals("duplicate", duplicate.status)
        assertEquals(mapOf("original" to first.id), duplicate.detail)
    }

    @Test
    fun `the bridge records failures and retries`() {
        var attempts = 0
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> ->
                    attempts++
                    if (attempts < 2) error("boom") else mapOf("ok" to true)
                },
            ),
        )

        val receipt = bridge.execute(
            decision(),
            ActionOption("a", Verb.ACT, "assign_team"),
            "operator",
            retry = RetryPolicy(attempts = 2),
        )

        assertEquals("executed", receipt.status)
        assertEquals(2, receipt.detail["attempts"])

        val failed = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> error("boom") },
            ),
        ).execute(decision(), ActionOption("a", Verb.ACT, "assign_team"), "operator")

        assertEquals("failed", failed.status)
        assertTrue(failed.error.orEmpty().contains("boom"))
    }

    @Test
    fun `the bridge can undo an executed receipt`() {
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> mapOf("ok" to true) },
            ),
            undoHandlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> mapOf("undone" to true) },
            ),
        )
        val receipt = bridge.execute(decision(), ActionOption("a", Verb.ACT, "assign_team"), "operator")

        val undone = bridge.undo(receipt.id, "operator")

        assertEquals("undone", undone.status)
        assertEquals(mapOf("undone" to true), undone.detail["undo"])
        assertEquals("undone", bridge.executionState()["assign_team"])
    }

    @Test
    fun `unknown receipts can be reconciled`() {
        val bridge = ExecutionBridge(
            handlers = mapOf(
                "assign_team" to { _: ActionOption, _: Map<String, Any?> -> emptyMap<String, Any?>() },
            ),
        )
        val receipt = bridge.execute(decision(), ActionOption("a", Verb.ACT, "assign_team"), "operator")
        val unknown = bridge.markUnknown(receipt.id, "operator", "timeout")
        assertEquals("unknown", unknown.status)

        val reconciled = bridge.reconcile(unknown.id, "operator", "executed", mapOf("provider" to "ok"))
        assertEquals("executed", reconciled.status)
        assertEquals("ok", reconciled.detail["provider"])
    }

    @Test
    fun `the runtime records decisions traces receipts and outcomes`() {
        val runtime = DecisionRuntime(
            bridge = ExecutionBridge(
                handlers = mapOf(
                    "assign_team" to { _: ActionOption, _: Map<String, Any?> -> mapOf("assigned" to true) },
                ),
            ),
        )
        val decision = runtime.decide(situation(), options(), mapOf("urgency" to 0.9))
        val receipt = runtime.execute(decision, actor = "operator")
        val outcome = runtime.measure(
            decision.decisionId,
            metric = "time_to_assessment",
            before = 10.0,
            after = 4.0,
            attributed = true,
            direction = "lower-better",
        )

        assertEquals("executed", receipt.status)
        assertEquals("helped", outcome.label)
        assertTrue(runtime.receipts().isNotEmpty())
        val trace = runtime.trace(decision.decisionId)
        assertTrue(trace.events.size >= 3)
        assertEquals(listOf("assign_team"), runtime.bridge.executionState().keys.toList())
        assertEquals(1, runtime.stats()["decisions"])
        assertNotNull(runtime.actionFor(decision))
    }

    @Test
    fun `the runtime turns approval failures into refused receipts`() {
        val runtime = DecisionRuntime(
            bridge = ExecutionBridge(
                handlers = mapOf(
                    "assign_team" to { _: ActionOption, _: Map<String, Any?> -> emptyMap<String, Any?>() },
                ),
            ),
        )
        val decision = runtime.decide(
            situation(),
            listOf(
                ActionOption(
                    "a-act",
                    Verb.ACT,
                    "assign_team",
                    expectedBenefit = 0.9,
                    requiresApproval = true,
                ),
            ),
            mapOf("urgency" to 0.9),
        )

        val receipt = runtime.execute(decision, actor = "operator")

        assertEquals("refused", receipt.status)
        assertTrue(receipt.error.orEmpty().contains("approval"))
        assertTrue(runtime.trace(decision.decisionId).events.any { it["stage"] == "approval.required" })
    }

    @Test
    fun `the client routes action requests through the runtime`() {
        val client = DecisionClient()
        val result = client.decide(
            DecisionRequest(
                subject = "demo",
                at = at,
                situation = situation(),
                options = options(),
                attributes = mapOf("urgency" to 0.9),
            ),
        )

        assertEquals(1, result.size)
        assertTrue(result.first().decisionId.startsWith("DEC-"))
        assertEquals(1, client.status()["decisions"])
        assertTrue(client.explain(result.first()).containsKey("reasonCode"))
    }

    @Test
    fun `the client routes explicit policies`() {
        val client = DecisionClient(
            policy = dev.laix.decision.policies.packs.SafetyConstrainedPolicy(),
        )
        val result = client.decide(
            DecisionRequest(
                subject = "demo",
                at = at,
                attributes = mapOf(
                    "risk_limit" to 0.2,
                    "options" to listOf(
                        mapOf("id" to "safe", "benefit" to 0.9, "risk" to 0.1),
                    ),
                ),
            ),
        )

        assertEquals("safe", result.first().actionId)
        assertEquals("safety-constrained.v1", client.status()["policy"])
        assertEquals(1, client.policies().size)
    }

    @Test
    fun `delivery records skipped receipts`() {
        val port = NullDelivery()
        val receipt = port.deliver(decision(), mapOf("text" to "hello"))

        assertEquals("skipped", receipt.status)
        assertEquals("DEC-1", receipt.decisionId)
        assertEquals(1, port.receipts.size)
        assertEquals(1, port.toMap()["receipts"].let { (it as List<*>).size })
    }

    @Test
    fun `a decision record is sealed approved and verified`() {
        val record = createRecord(
            title = "Assign the team",
            decision = "Assign the on-call team",
            evidence = listOf(EvidenceRef(id = "e-1", kind = "log")),
            metadata = mapOf("ticket" to "T-1"),
        )

        assertEquals("draft", record.status)
        assertTrue(verify(record))
        val approved = approve(record, by = "lead", note = "ok")
        assertEquals("approved", approved.status)
        assertEquals("approved", approved.approval.state)
        assertTrue(verify(approved))
        val executed = markExecuted(approved, by = "operator")
        assertEquals("executed", executed.status)
        assertTrue(verify(executed))
        val undone = undo(executed, by = "operator")
        assertEquals("undone", undone.status)
        assertTrue(!undone.undo.available)
        assertTrue(verify(undone))
    }

    @Test
    fun `a decision record can be rejected only while a draft`() {
        val record = createRecord(
            title = "T",
            decision = "D",
            evidence = listOf(EvidenceRef(id = "e-1")),
        )
        val rejected = reject(record, by = "lead", note = "no")
        assertEquals("rejected", rejected.status)
        assertFailsWith<IllegalArgumentException> { approve(rejected, by = "lead") }
        assertFailsWith<IllegalArgumentException> {
            createRecord(title = " ", decision = "D", evidence = listOf(EvidenceRef(id = "e")))
        }
        assertFailsWith<IllegalArgumentException> {
            createRecord(title = "T", decision = "D", evidence = emptyList())
        }
    }

    @Test
    fun `experience state merges beliefs and round-trips snapshots`() {
        val state = ExperienceState(subject = "demo")
        val belief = state.observe(
            Observation(
                id = "o-1",
                at = at,
                source = "sensor",
                kind = "reading",
                confidence = 0.6,
                payload = mapOf("proposition" to "door-open", "statement" to "the door is open"),
            ),
        )
        assertNotNull(belief)
        assertEquals(0.6, belief.confidence)
        assertEquals("medium", state.band("door-open"))

        state.setBelief(
            Belief(id = "other", proposition = "other", confidence = 0.9, updatedAt = at),
        )
        state.record(
            Decision(
                verb = Verb.ACT,
                confidence = 0.9,
                reasonCode = "x",
                rationale = "x",
                decisionId = "D",
                createdAt = at,
            ),
        )
        assertEquals("act", state.phase)

        val snapshot = state.snapshot()
        val restored = ExperienceState.fromSnapshot(snapshot)
        assertEquals("demo", restored.subject)
        assertEquals("other", restored.beliefs.keys.last())
        assertEquals(state.confidence(), restored.confidence())

        val store = InMemoryStateStore()
        store.save("demo", state)
        assertEquals("demo", store.load("demo")?.subject)
        store.delete("demo")
        assertEquals(null, store.load("demo"))
    }

    @Test
    fun `experience state expires beliefs`() {
        val state = ExperienceState(subject = "demo")
        state.setBelief(
            Belief(
                id = "old",
                proposition = "old",
                confidence = 0.8,
                updatedAt = at,
                expiresAt = "2026-11-01T09:00:00+00:00",
            ),
        )

        val removed = state.expire(java.time.OffsetDateTime.parse(at))

        assertEquals(listOf("old"), removed)
        assertTrue(state.beliefs.isEmpty())
    }
}
