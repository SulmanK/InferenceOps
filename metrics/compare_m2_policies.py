#!/usr/bin/env python3
"""Normalize Milestone 2 policy replay summaries into comparison artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        if not path.is_dir():
            raise


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def parse_policy_and_scenario(summary: dict[str, Any], fallback_run_id: str) -> tuple[str, str]:
    scenario = Path(str(summary.get("trace", ""))).stem
    run_id = str(summary.get("run_id") or fallback_run_id)
    if not scenario:
        raise ValueError(f"cannot infer scenario from run_id={run_id}")
    suffix = f"_{scenario}"
    if not run_id.endswith(suffix):
        raise ValueError(f"run_id does not end with scenario suffix: {run_id}")
    policy_part = run_id[: -len(suffix)]
    policy = policy_part.rsplit("_", 1)[-1]
    if policy == "two" and policy_part.endswith("power_of_two"):
        policy = "power_of_two"
    if policy == "aware" and policy_part.endswith("cache_aware"):
        policy = "cache_aware"
    if policy == "robin" and policy_part.endswith("round_robin"):
        policy = "round_robin"
    return policy, scenario


def collect_rows(replay_dir: Path, run_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(replay_dir.glob(f"replay_summary_{run_id}_*.json")):
        summary = load_json(path)
        policy, scenario = parse_policy_and_scenario(summary, run_id)
        rows.append(
            {
                "run_id": run_id,
                "policy": policy,
                "scenario": scenario,
                "requests": summary.get("requests"),
                "successful": summary.get("successful"),
                "failed": summary.get("failed"),
                "latency_ms_p50": summary.get("latency_ms_p50"),
                "latency_ms_p95": summary.get("latency_ms_p95"),
                "latency_ms_p99": summary.get("latency_ms_p99"),
                "latency_ms_mean": summary.get("latency_ms_mean"),
                "duration_s": summary.get("duration_s"),
                "trace_sha256": summary.get("trace_sha256"),
                "summary_path": str(path),
            }
        )
    if not rows:
        raise FileNotFoundError(f"no replay_summary files found for run_id={run_id} in {replay_dir}")
    return rows


def best_by_scenario(rows: list[dict[str, Any]], metric: str) -> dict[str, dict[str, Any]]:
    winners: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = row.get(metric)
        if value is None:
            continue
        scenario = str(row["scenario"])
        if scenario not in winners or value < winners[scenario][metric]:
            winners[scenario] = row
    return winners


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run_id",
        "policy",
        "scenario",
        "requests",
        "successful",
        "failed",
        "latency_ms_p50",
        "latency_ms_p95",
        "latency_ms_p99",
        "latency_ms_mean",
        "duration_s",
        "trace_sha256",
        "summary_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-dir", type=Path, default=Path("artifacts/m2/replay"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("results/milestone3"))
    parser.add_argument("--metric", default="latency_ms_p95")
    args = parser.parse_args()

    ensure_dir(args.out_dir)
    rows = collect_rows(args.replay_dir, args.run_id)
    rows = sorted(rows, key=lambda row: (row["scenario"], row["policy"]))
    winners = best_by_scenario(rows, args.metric)

    csv_path = args.out_dir / f"policy_comparison_{args.run_id}.csv"
    json_path = args.out_dir / f"policy_comparison_{args.run_id}.json"
    write_csv(csv_path, rows)
    json_path.write_text(
        json.dumps(
            {
                "milestone": "m3",
                "source_milestone": "m2",
                "run_id": args.run_id,
                "metric": args.metric,
                "rows": rows,
                "best_by_scenario": winners,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
