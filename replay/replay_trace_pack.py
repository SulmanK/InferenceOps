#!/usr/bin/env python3
"""Replay every selected scenario in a trace pack."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("scenarios"), list):
        raise ValueError(f"{path} is not a trace-pack manifest")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("traces/pack_v1/manifest.json"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--api-key", default="local-dev")
    parser.add_argument("--out", type=Path, default=Path("artifacts/m1/replay"))
    parser.add_argument("--run-id", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--time-scale", type=float, default=1.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--scenarios",
        default="",
        help="Comma-separated scenario names. Defaults to every scenario in the manifest.",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    requested = {s.strip() for s in args.scenarios.split(",") if s.strip()}
    scenarios = [
        scenario
        for scenario in manifest["scenarios"]
        if not requested or scenario.get("name") in requested
    ]
    if requested:
        found = {scenario.get("name") for scenario in scenarios}
        missing = sorted(requested - found)
        if missing:
            raise SystemExit(f"missing scenarios in manifest: {', '.join(missing)}")

    args.out.mkdir(parents=True, exist_ok=True)
    replay_script = Path(__file__).with_name("replay_trace.py")
    batch_results: list[dict[str, Any]] = []

    for scenario in scenarios:
        scenario_name = scenario["name"]
        scenario_run_id = f"{args.run_id}_{scenario_name}"
        command = [
            sys.executable,
            str(replay_script),
            "--trace",
            scenario["path"],
            "--base-url",
            args.base_url,
            "--model",
            args.model,
            "--api-key",
            args.api_key,
            "--out",
            str(args.out),
            "--run-id",
            scenario_run_id,
            "--time-scale",
            str(args.time_scale),
        ]
        if args.dry_run:
            command.append("--dry-run")

        print(f"Replaying {scenario_name} run_id={scenario_run_id}")
        completed = subprocess.run(command, check=False)
        summary_path = args.out / f"replay_summary_{scenario_run_id}.json"
        summary: dict[str, Any] = {}
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        batch_results.append(
            {
                "scenario": scenario_name,
                "run_id": scenario_run_id,
                "returncode": completed.returncode,
                "summary_path": str(summary_path),
                "summary": summary,
            }
        )

    batch_summary = {
        "milestone": "m1",
        "run_id": args.run_id,
        "manifest": str(args.manifest),
        "trace_pack": manifest.get("trace_pack"),
        "model": args.model,
        "base_url": args.base_url,
        "time_scale": args.time_scale,
        "dry_run": args.dry_run,
        "scenarios": batch_results,
    }
    batch_path = args.out / f"trace_pack_replay_summary_{args.run_id}.json"
    batch_path.write_text(json.dumps(batch_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {batch_path}")

    return 0 if all(result["returncode"] == 0 for result in batch_results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

