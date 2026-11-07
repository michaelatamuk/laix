# Copyright Sierra
"""Tool-calling agent with a LAIX approval guardrail on mutating calls."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from litellm import completion

if os.environ.get("LAIX_SRC"):
    sys.path.insert(0, os.environ["LAIX_SRC"])

from laix import ActionOption, DecisionProblem, LiveDecisionEngine
from tau_bench.agents.base import Agent
from tau_bench.envs.base import Env
from tau_bench.types import RESPOND_ACTION_NAME, Action, SolveResult

MUTATING = {
    "exchange_delivered_order_items",
    "return_delivered_order_items",
    "modify_pending_order_items",
    "modify_pending_order_address",
    "modify_pending_order_payment",
    "modify_user_address",
    "cancel_pending_order",
    "update_reservation_baggages",
    "update_reservation_flights",
    "update_reservation_passengers",
    "cancel_reservation",
    "book_reservation",
}
CONFIRM_WORDS = ("yes", "confirm", "go ahead", "proceed", "sure", "please do", "okay", "ok")


class LAIXGuardrailAgent(Agent):
    def __init__(
        self,
        tools_info: list[dict[str, Any]],
        wiki: str,
        model: str,
        provider: str,
        temperature: float = 0.0,
    ):
        self.tools_info = tools_info
        self.wiki = wiki
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self._engine = LiveDecisionEngine()
        self._asked: set[str] = set()

    def _last_user_text(self, messages: list[dict[str, Any]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return str(message.get("content", "")).lower()
        return ""

    def _confirmed(self, messages: list[dict[str, Any]]) -> bool:
        text = self._last_user_text(messages)
        return any(word in text for word in CONFIRM_WORDS)

    def _guard(self, action: Action, messages: list[dict[str, Any]]) -> str:
        if action.name not in MUTATING:
            return "act"
        if self._confirmed(messages):
            return "act"

        options = (
            ActionOption(
                id="act",
                verb="act",
                name=action.name,
                expected_benefit=0.9,
                risk=0.5,
                reversible=False,
                requires_approval=True,
                interrupt_cost=0.4,
            ),
            ActionOption(
                id="ask",
                verb="ask",
                name="ask the user to confirm",
                expected_benefit=0.75,
                risk=0.0,
                reversible=True,
                interrupt_cost=0.2,
            ),
            ActionOption(
                id="escalate",
                verb="escalate",
                name="transfer to a human agent",
                expected_benefit=0.2,
                risk=0.0,
                reversible=True,
                interrupt_cost=0.4,
            ),
        )
        plan = self._engine.solve(
            DecisionProblem(
                subject=action.name,
                at="2026-11-01T10:00:00+00:00",
                options=options,
                attributes={"approvals": {"act": "pending"}},
            )
        )
        if plan.requires_approval or plan.action_id in {"ask", "escalate"}:
            self._asked.add(action.name)
            return "ask"
        return "act"

    def solve(
        self,
        env: Env,
        task_index: int | None = None,
        max_num_steps: int = 30,
    ) -> SolveResult:
        total_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        reward = 0.0
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.wiki},
            {"role": "user", "content": obs},
        ]
        for _ in range(max_num_steps):
            res = completion(
                messages=messages,
                model=self.model,
                custom_llm_provider=self.provider,
                tools=self.tools_info,
                temperature=self.temperature,
            )
            next_message = res.choices[0].message.model_dump()
            total_cost += res._hidden_params["response_cost"] or 0
            action = self._message_to_action(next_message)
            decision = self._guard(action, messages)

            if decision == "ask":
                tool_call = next_message["tool_calls"][0]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "content": (
                                "Approval required. Ask the user to confirm this action "
                                "before it is executed."
                            ),
                        },
                    ]
                )
                continue

            env_response = env.step(action)
            reward = env_response.reward
            info = {**info, **env_response.info.model_dump()}
            if action.name != RESPOND_ACTION_NAME:
                next_message["tool_calls"] = next_message["tool_calls"][:1]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": env_response.observation,
                        },
                    ]
                )
            else:
                messages.extend(
                    [
                        next_message,
                        {"role": "user", "content": env_response.observation},
                    ]
                )
            if env_response.done:
                break
        return SolveResult(
            reward=reward,
            info=info,
            messages=messages,
            total_cost=total_cost,
        )

    @staticmethod
    def _message_to_action(message: dict[str, Any]) -> Action:
        if (
            "tool_calls" in message
            and message["tool_calls"] is not None
            and len(message["tool_calls"]) > 0
            and message["tool_calls"][0]["function"] is not None
        ):
            tool_call = message["tool_calls"][0]
            return Action(
                name=tool_call["function"]["name"],
                kwargs=json.loads(tool_call["function"]["arguments"]),
            )
        return Action(name=RESPOND_ACTION_NAME, kwargs={"content": message["content"]})
