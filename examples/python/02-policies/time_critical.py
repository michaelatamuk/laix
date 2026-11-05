"""Water and electricity: hard gates first, then a multi-factor score.

Two runs show how confidence changes the answer. The hard risk limit and the
6-minute window run before scoring; the score then trades benefit against risk,
delay, money, disruption and the value of looking first.
"""

from laix import DecisionRequest, Intent, Layer, Decision

WINDOW_MINUTES = 6
RISK_LIMIT = 0.20

WEIGHTS = {
    "risk": 0.25,
    "delay": 0.05,
    "cost": 0.002,
    "disruption": 0.15,
    "information": 0.20,
}

OPTIONS = (
    {
        "id": "breaker-wet",
        "verb": "act",
        "name": "cross the wet floor to the breaker",
        "benefit": 1.00,
        "risk": 0.90,
        "delay_minutes": 0,
        "cost": 0.0,
        "disruption": 0.0,
    },
    {
        "id": "breaker-dry",
        "verb": "act",
        "name": "use the dry corridor to the breaker",
        "benefit": 0.85,
        "risk": 0.10,
        "delay_minutes": 4,
        "cost": 0.0,
        "disruption": 0.10,
    },
    {
        "id": "electrician",
        "verb": "escalate",
        "name": "call an electrician",
        "benefit": 0.70,
        "risk": 0.00,
        "delay_minutes": 15,
        "cost": 120.0,
        "disruption": 0.05,
    },
    {
        "id": "evacuate",
        "verb": "guide",
        "name": "keep people out and raise the alarm",
        "benefit": 0.60,
        "risk": 0.03,
        "delay_minutes": 1,
        "cost": 0.0,
        "disruption": 0.50,
    },
    {
        "id": "look",
        "verb": "observe",
        "name": "look from the doorway",
        "benefit": 0.50,
        "risk": 0.05,
        "delay_minutes": 2,
        "cost": 0.0,
        "disruption": 0.0,
        "information_gain": 1.0,
    },
    {
        "id": "wait",
        "verb": "wait",
        "name": "wait",
        "benefit": 0.10,
        "risk": 0.00,
        "delay_minutes": 0,
        "cost": 0.0,
        "disruption": 0.0,
    },
)


class TradeoffPolicy:
    name = "water-electricity.v2"
    version = "2.0"

    def decide(self, request: DecisionRequest) -> list[Decision]:
        confidence = float(request.attributes.get("confidence", 0.80))
        applied: list[str] = []
        eligible: list[dict] = []

        for option in OPTIONS:
            if option["risk"] > RISK_LIMIT:
                applied.append(
                    f"{option['id']} blocked by risk "
                    f"{option['risk']:.2f} > {RISK_LIMIT:.2f}"
                )
                continue
            if option["delay_minutes"] > WINDOW_MINUTES:
                applied.append(
                    f"{option['id']} misses the {WINDOW_MINUTES}-minute window "
                    f"({option['delay_minutes']} min)"
                )
                continue
            eligible.append(option)

        def score(option: dict) -> float:
            return (
                confidence * option["benefit"]
                - WEIGHTS["risk"] * option["risk"]
                - WEIGHTS["delay"] * option["delay_minutes"]
                - WEIGHTS["cost"] * option["cost"]
                - WEIGHTS["disruption"] * option["disruption"]
                + WEIGHTS["information"]
                * option.get("information_gain", 0.0)
                * (1.0 - confidence)
            )

        ranked = sorted(eligible, key=score, reverse=True)
        best = ranked[0]
        alternatives = tuple(
            {
                "action_id": option["id"],
                "score": round(score(option), 4),
                "rejected_because": (
                    "selected"
                    if option["id"] == best["id"]
                    else f"outranked by {best['id']}"
                ),
            }
            for option in ranked
        )

        return [
            Decision(
                verb=best["verb"],
                confidence=confidence,
                reason_code="tradeoff_score",
                rationale=(
                    f"{best['name']}: benefit {best['benefit']:.2f} at confidence "
                    f"{confidence:.2f}, risk {best['risk']:.2f}, delay "
                    f"{best['delay_minutes']} min"
                ),
                action_id=best["id"],
                score=round(score(best), 4),
                alternatives=alternatives,
                constraints_applied=tuple(applied),
                intent=(
                    Intent(
                        "handover",
                        {
                            "target": "electrician",
                            "reason": "check the socket after the immediate action",
                        },
                    )
                    if best["id"] != "electrician"
                    else None
                ),
            )
        ]


def run(confidence: float) -> None:
    decision = Layer(policy=TradeoffPolicy()).decide(
        DecisionRequest(
            subject="water near electricity",
            at="2026-11-01T10:00:00+00:00",
            attributes={"confidence": confidence},
        )
    )[0]
    print(
        f"confidence {confidence:.2f}: "
        f"{decision.verb} {decision.action_id} {decision.score}"
    )
    for item in decision.alternatives:
        print(" ", item["action_id"], item["score"], item["rejected_because"])
    for item in decision.constraints_applied:
        print("  gate", item)
    print()


run(0.80)
run(0.45)
