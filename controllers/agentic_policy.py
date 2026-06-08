"""Agentic controller with bounded action validation."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import asdict, dataclass
from typing import Protocol

try:
    from policies import ALLOWED_POLICIES, Action, Observation, ScenarioHeuristicController
except ImportError:  # pragma: no cover - package import path.
    from controllers.policies import ALLOWED_POLICIES, Action, Observation, ScenarioHeuristicController


class AgentClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Return the agent's raw response."""


@dataclass(frozen=True)
class AgentDecision:
    action: Action
    raw_response: str
    valid: bool
    fallback_used: bool
    error: str | None = None


class ScriptedAgentClient:
    """Deterministic stand-in for offline agent evaluation and tests."""

    def complete(self, prompt: str) -> str:
        payload = json.loads(prompt)
        scenario = payload.get("observation", {}).get("scenario")
        if scenario == "shared_prefix_burst":
            policy = "cache_aware"
            reason = "shared prefix locality is the dominant signal"
        elif scenario == "mixed_short_long":
            policy = "power_of_two"
            reason = "mixed request sizes need load-sensitive routing"
        elif scenario == "degraded_worker":
            policy = "power_of_two"
            reason = "worker degradation signal should bias away from overloaded workers"
        else:
            policy = "round_robin"
            reason = "no specialized signal is present"
        return json.dumps({"policy": policy, "reason": reason})


class OpenAICompatibleClient:
    """Minimal OpenAI-compatible chat client using only the standard library."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("AGENT_OPENAI_BASE_URL") or "https://api.openai.com").rstrip("/")
        self.api_key = api_key or os.environ.get("AGENT_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("AGENT_MODEL") or "gpt-4.1-mini"
        self.timeout_s = timeout_s
        if not self.api_key:
            raise ValueError("missing AGENT_OPENAI_API_KEY or OPENAI_API_KEY")

    def complete(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a bounded LLM serving router controller. "
                        "Return only JSON with keys policy and reason. "
                        f"policy must be one of: {', '.join(sorted(ALLOWED_POLICIES))}."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


class AgenticPolicyController:
    name = "agentic_controller"

    def __init__(
        self,
        client: AgentClient,
        fallback_policy: str = "cache_aware",
    ) -> None:
        if fallback_policy not in ALLOWED_POLICIES:
            raise ValueError(f"unsupported fallback policy: {fallback_policy}")
        self.client = client
        self.fallback_policy = fallback_policy
        self._last_decision: AgentDecision | None = None

    @property
    def last_decision(self) -> AgentDecision | None:
        return self._last_decision

    def choose(self, observation: Observation) -> Action:
        decision = self.decide(observation)
        return decision.action

    def decide(self, observation: Observation) -> AgentDecision:
        prompt = build_agent_prompt(observation)
        try:
            raw = self.client.complete(prompt)
            action = parse_agent_action(raw)
            decision = AgentDecision(action=action, raw_response=raw, valid=True, fallback_used=False)
        except Exception as exc:  # noqa: BLE001 - guardrail records invalid agent output.
            fallback = Action(self.fallback_policy, f"fallback after invalid agent response: {type(exc).__name__}")
            decision = AgentDecision(
                action=fallback,
                raw_response=locals().get("raw", ""),
                valid=False,
                fallback_used=True,
                error=str(exc),
            )
        self._last_decision = decision
        return decision


def build_agent_prompt(observation: Observation) -> str:
    return json.dumps(
        {
            "task": "choose exactly one serving router policy",
            "allowed_policies": sorted(ALLOWED_POLICIES),
            "observation": asdict(observation),
            "output_contract": {"policy": "string", "reason": "short string"},
        },
        sort_keys=True,
    )


def parse_agent_action(raw_response: str) -> Action:
    data = json.loads(extract_json_object(raw_response))
    if not isinstance(data, dict):
        raise ValueError("agent response is not a JSON object")
    policy = data.get("policy")
    reason = data.get("reason")
    if not isinstance(policy, str):
        raise ValueError("agent policy is missing or not a string")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("agent reason is missing or not a non-empty string")
    return Action(policy=policy, reason=reason.strip())


def extract_json_object(raw_response: str) -> str:
    text = raw_response.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("agent response does not contain a JSON object")
    return text[start : end + 1]


def build_agent_controller(mode: str) -> AgenticPolicyController:
    if mode == "scripted":
        return AgenticPolicyController(ScriptedAgentClient())
    if mode == "openai-compatible":
        return AgenticPolicyController(OpenAICompatibleClient())
    if mode == "heuristic-shadow":
        return AgenticPolicyController(HeuristicShadowClient())
    raise ValueError(f"unknown agent mode: {mode}")


class HeuristicShadowClient:
    """Adapter that emits JSON from the non-agentic heuristic for A/B plumbing tests."""

    def __init__(self) -> None:
        self.heuristic = ScenarioHeuristicController()

    def complete(self, prompt: str) -> str:
        payload = json.loads(prompt)
        observation = Observation(**payload["observation"])
        action = self.heuristic.choose(observation)
        return json.dumps({"policy": action.policy, "reason": action.reason})

