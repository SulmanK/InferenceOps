#!/usr/bin/env python3
"""Evaluate bounded Milestone 3 controllers against observed policy results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from policies import (
        ScenarioHeuristicController,
        StaticPolicyController,
        TailGuardController,
        observation_for_scenario,
    )
except ImportError:  # pragma: no cover - package import path.
    from controllers.policies import (
        ScenarioHeuristicController,
        StaticPolicyController,
        TailGuardController,
        observation_for_scenario,
    )


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
        "# Milestone 3 Controller Evaluation",
        "",
        f"Source run: `{result['source_run_id']}`",
        "",
        "| Controller | Scenario | Chosen Policy | Best Policy | P95 ms | Best P95 ms | Regret ms | Reason |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in result["evaluations"]:
        lines.append(
            "| {controller} | `{scenario}` | `{chosen_policy}` | `{best_policy}` | {chosen_p95:.2f} | {best_p95:.2f} | {regret_ms:.2f} | {reason} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "Lower regret means the controller chose closer to the best observed policy for that scenario.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/milestone3"))
    parser.add_argument("--metric", default="latency_ms_p95")
    args = parser.parse_args()

    comparison = load_json(args.comparison)
    rows = comparison["rows"]
    by_scenario_policy = index_rows(rows)
    best_by_scenario = comparison["best_by_scenario"]
    scenarios = sorted(best_by_scenario)
    controllers = [
        StaticPolicyController("round_robin"),
        StaticPolicyController("cache_aware"),
        StaticPolicyController("power_of_two"),
        ScenarioHeuristicController(),
        TailGuardController(),
    ]

    evaluations: list[dict[str, Any]] = []
    for controller in controllers:
        for scenario in scenarios:
            best_row = best_by_scenario[scenario]
            observation = observation_for_scenario(
                scenario,
                p95_latency_ms=best_row.get(args.metric),
            )
            action = controller.choose(observation)
            chosen_row = by_scenario_policy[(scenario, action.policy)]
            chosen_value = float(chosen_row[args.metric])
            best_value = float(best_row[args.metric])
            evaluations.append(
                {
                    "controller": controller.name,
                    "scenario": scenario,
                    "chosen_policy": action.policy,
                    "best_policy": best_row["policy"],
                    "chosen_p95": chosen_value,
                    "best_p95": best_value,
                    "regret_ms": chosen_value - best_value,
                    "reason": action.reason,
                }
            )

    by_controller: dict[str, dict[str, float]] = {}
    for row in evaluations:
        stats = by_controller.setdefault(row["controller"], {"total_regret_ms": 0.0, "choices": 0.0})
        stats["total_regret_ms"] += row["regret_ms"]
        stats["choices"] += 1.0
    for stats in by_controller.values():
        stats["mean_regret_ms"] = stats["total_regret_ms"] / stats["choices"]

    result = {
        "milestone": "m3",
        "source_run_id": comparison["run_id"],
        "metric": args.metric,
        "evaluations": evaluations,
        "controller_summary": by_controller,
    }

    ensure_dir(args.out_dir)
    run_id = comparison["run_id"]
    json_path = args.out_dir / f"controller_evaluation_{run_id}.json"
    md_path = args.out_dir / f"controller_evaluation_{run_id}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(result), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
