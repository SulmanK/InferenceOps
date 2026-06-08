#!/usr/bin/env python3
"""Evaluate an agentic controller against observed policy results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from agentic_policy import build_agent_controller
    from policies import observation_for_scenario
except ImportError:  # pragma: no cover - package import path.
    from controllers.agentic_policy import build_agent_controller
    from controllers.policies import observation_for_scenario


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        if not path.is_dir():
            raise


def index_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["scenario"]), str(row["policy"])): row for row in rows}


def format_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Milestone 4 Agentic Controller Evaluation",
        "",
        f"Source run: `{result['source_run_id']}`",
        f"Agent mode: `{result['agent_mode']}`",
        "",
        "| Scenario | Agent Policy | Best Policy | Valid | Fallback | P95 ms | Best P95 ms | Regret ms | Reason |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["evaluations"]:
        lines.append(
            "| `{scenario}` | `{chosen_policy}` | `{best_policy}` | {valid} | {fallback_used} | {chosen_p95:.2f} | {best_p95:.2f} | {regret_ms:.2f} | {reason} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "The agent is only credited for bounded, valid actions. Invalid output uses the safe fallback policy and is recorded.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--agent-mode", choices=("scripted", "heuristic-shadow", "openai-compatible"), default="scripted")
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts/m4"))
    parser.add_argument("--metric", default="latency_ms_p95")
    args = parser.parse_args()

    comparison = load_json(args.comparison)
    rows = comparison["rows"]
    by_scenario_policy = index_rows(rows)
    best_by_scenario = comparison["best_by_scenario"]
    scenarios = sorted(best_by_scenario)
    controller = build_agent_controller(args.agent_mode)

    evaluations: list[dict[str, Any]] = []
    for scenario in scenarios:
        observation = observation_for_scenario(scenario)
        decision = controller.decide(observation)
        best_row = best_by_scenario[scenario]
        chosen_row = by_scenario_policy[(scenario, decision.action.policy)]
        chosen_value = float(chosen_row[args.metric])
        best_value = float(best_row[args.metric])
        evaluations.append(
            {
                "scenario": scenario,
                "chosen_policy": decision.action.policy,
                "best_policy": best_row["policy"],
                "valid": decision.valid,
                "fallback_used": decision.fallback_used,
                "chosen_p95": chosen_value,
                "best_p95": best_value,
                "regret_ms": chosen_value - best_value,
                "reason": decision.action.reason,
                "error": decision.error,
                "raw_response": decision.raw_response,
            }
        )

    result = {
        "milestone": "m4",
        "source_run_id": comparison["run_id"],
        "agent_mode": args.agent_mode,
        "metric": args.metric,
        "evaluations": evaluations,
        "summary": {
            "choices": len(evaluations),
            "invalid_actions": sum(1 for row in evaluations if not row["valid"]),
            "fallbacks": sum(1 for row in evaluations if row["fallback_used"]),
            "total_regret_ms": sum(float(row["regret_ms"]) for row in evaluations),
            "mean_regret_ms": sum(float(row["regret_ms"]) for row in evaluations) / len(evaluations),
        },
    }

    ensure_dir(args.out_dir)
    run_id = comparison["run_id"]
    json_path = args.out_dir / f"agentic_evaluation_{run_id}_{args.agent_mode}.json"
    md_path = args.out_dir / f"agentic_evaluation_{run_id}_{args.agent_mode}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(result), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

