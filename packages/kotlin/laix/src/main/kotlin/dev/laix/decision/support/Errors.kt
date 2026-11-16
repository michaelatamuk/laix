package dev.laix.decision.support

/** A policy returned something the decision contract cannot accept. */
class DecisionPolicyError(message: String) : RuntimeException(message)
