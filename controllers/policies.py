"""Bounded policy controllers for Milestone 3."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


ALLOWED_POLICIES = frozenset({"round_robin", "cache_aware", "power_of_two"})


@dataclass(frozen=True)
class Observation:
    """Normalized controller input for one scenario/control interval."""

    scenario: str
    shared_prefix_ratio: float = 0.0
    long_request_ratio: float = 0.0
    degraded_worker_signal: float = 0.0
    p95_latency_ms: float | None = None
    p95_slo_ms: float | None = None


@dataclass(frozen=True)
class Action:
    """Finite controller action."""

    policy: str
    reason: str

    def __post_init__(self) -> None:
        if self.policy not in ALLOWED_POLICIES:
            raise ValueError(f"unsupported policy action: {self.policy}")


class Controller(Protocol):
    name: str

    def choose(self, observation: Observation) -> Action:
        """Return one bounded policy action."""


@dataclass(frozen=True)
class StaticPolicyController:
    policy: str

    @property
    def name(self) -> str:
        return f"static_{self.policy}"

    def choose(self, observation: Observation) -> Action:
        return Action(self.policy, "fixed baseline policy")


class ScenarioHeuristicController:
    name = "scenario_heuristic"

    def choose(self, observation: Observation) -> Action:
        if observation.degraded_worker_signal >= 0.5 or observation.scenario == "degraded_worker":
            return Action("power_of_two", "prefer load-sensitive routing when a worker looks degraded")
        if observation.shared_prefix_ratio >= 0.5 or observation.scenario == "shared_prefix_burst":
            return Action("cache_aware", "prefer cache locality for repeated-prefix traffic")
        if observation.long_request_ratio >= 0.3 or observation.scenario == "mixed_short_long":
            return Action("power_of_two", "protect short requests from long-prefill imbalance")
        return Action("round_robin", "fallback when no strong signal is present")


class TailGuardController:
    name = "tail_guard"

    def choose(self, observation: Observation) -> Action:
        if (
            observation.p95_latency_ms is not None
            and observation.p95_slo_ms is not None
            and observation.p95_latency_ms > observation.p95_slo_ms
        ):
            return Action("power_of_two", "p95 latency is over SLO; prefer load-sensitive routing")
        if observation.shared_prefix_ratio >= 0.7:
            return Action("cache_aware", "strong prefix locality signal")
        if observation.degraded_worker_signal >= 0.25:
            return Action("power_of_two", "possible worker degradation")
        return Action("round_robin", "latency is within guardrail")


def observation_for_scenario(scenario: str, p95_latency_ms: float | None = None) -> Observation:
    """Build a deterministic first-pass observation from a trace scenario name."""

    if scenario == "shared_prefix_burst":
        return Observation(
            scenario=scenario,
            shared_prefix_ratio=0.85,
            long_request_ratio=0.1,
            degraded_worker_signal=0.0,
            p95_latency_ms=p95_latency_ms,
            p95_slo_ms=250.0,
        )
    if scenario == "mixed_short_long":
        return Observation(
            scenario=scenario,
            shared_prefix_ratio=0.15,
            long_request_ratio=0.35,
            degraded_worker_signal=0.0,
            p95_latency_ms=p95_latency_ms,
            p95_slo_ms=300.0,
        )
    if scenario == "degraded_worker":
        return Observation(
            scenario=scenario,
            shared_prefix_ratio=0.25,
            long_request_ratio=0.15,
            degraded_worker_signal=0.75,
            p95_latency_ms=p95_latency_ms,
            p95_slo_ms=250.0,
        )
    return Observation(scenario=scenario, p95_latency_ms=p95_latency_ms, p95_slo_ms=250.0)

