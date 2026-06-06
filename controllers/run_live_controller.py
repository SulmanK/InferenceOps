#!/usr/bin/env python3
"""Run a bounded controller against a live SGLang Gateway topology."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from policies import (
        Controller,
        ScenarioHeuristicController,
        StaticPolicyController,
        TailGuardController,
        observation_for_scenario,
    )
except ImportError:  # pragma: no cover - package import path.
    from controllers.policies import (
        Controller,
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


def build_controller(name: str) -> Controller:
    if name.startswith("static_"):
        return StaticPolicyController(name.removeprefix("static_"))
    if name == "scenario_heuristic":
        return ScenarioHeuristicController()
    if name == "tail_guard":
        return TailGuardController()
    raise ValueError(f"unknown controller: {name}")


def run_command(command: list[str], env: dict[str, str] | None = None) -> int:
    print("+ " + " ".join(command), flush=True)
    return subprocess.run(command, check=False, env=env).returncode


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--controller", default="scenario_heuristic")
    parser.add_argument("--manifest", type=Path, default=Path("traces/pack_v1/manifest.json"))
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--base-url", default="http://127.0.0.1:30000")
    parser.add_argument("--out", type=Path, default=Path("artifacts/m3/live"))
    parser.add_argument("--run-id", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--time-scale", type=float, default=1.0)
    parser.add_argument("--gateway-port", default="30000")
    parser.add_argument("--worker1-port", default="31001")
    parser.add_argument("--worker2-port", default="31002")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = load_json(args.manifest)
    scenarios = manifest.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError(f"{args.manifest} does not contain a scenario list")

    controller = build_controller(args.controller)
    actions: list[dict[str, Any]] = []
    scenario_results: list[dict[str, Any]] = []
    replay_script = Path("replay/replay_trace.py")

    args.out.mkdir(parents=True, exist_ok=True)

    for scenario in scenarios:
        scenario_name = scenario["name"]
        observation = observation_for_scenario(scenario_name)
        action = controller.choose(observation)
        scenario_run_id = f"{args.run_id}_{controller.name}_{scenario_name}"
        action_row = {
            "scenario": scenario_name,
            "controller": controller.name,
            "policy": action.policy,
            "reason": action.reason,
            "run_id": scenario_run_id,
            "observation": observation.__dict__,
        }
        actions.append(action_row)
        print(
            f"controller={controller.name} scenario={scenario_name} policy={action.policy} reason={action.reason}",
            flush=True,
        )

        if args.dry_run:
            scenario_results.append(
                {
                    "scenario": scenario_name,
                    "run_id": scenario_run_id,
                    "returncode": 0,
                    "summary_path": None,
                    "summary": {},
                }
            )
            continue

        stop_code = run_command(["bash", "deploy/sglang/m2_stop_gateway.sh"])
        if stop_code != 0:
            return stop_code

        gateway_env = {
            **dict(os.environ),
            "POLICY": action.policy,
            "GATEWAY_PORT": args.gateway_port,
            "WORKER1_PORT": args.worker1_port,
            "WORKER2_PORT": args.worker2_port,
        }
        start_code = run_command(["bash", "deploy/sglang/m2_start_gateway.sh"], env=gateway_env)
        if start_code != 0:
            return start_code

        wait_code = run_command(
            [
                "bash",
                "deploy/sglang/m2_wait_for_endpoint.sh",
                f"http://127.0.0.1:{args.gateway_port}/v1/models",
                "300",
            ]
        )
        if wait_code != 0:
            return wait_code

        replay_code = run_command(
            [
                sys.executable,
                str(replay_script),
                "--trace",
                scenario["path"],
                "--base-url",
                args.base_url,
                "--model",
                args.model,
                "--out",
                str(args.out),
                "--run-id",
                scenario_run_id,
                "--time-scale",
                str(args.time_scale),
            ]
        )
        summary_path = args.out / f"replay_summary_{scenario_run_id}.json"
        summary = load_json(summary_path) if summary_path.exists() else {}
        scenario_results.append(
            {
                "scenario": scenario_name,
                "run_id": scenario_run_id,
                "returncode": replay_code,
                "summary_path": str(summary_path),
                "summary": summary,
            }
        )
        if replay_code != 0:
            return replay_code

    if not args.dry_run:
        run_command(["bash", "deploy/sglang/m2_stop_gateway.sh"])

    report = {
        "milestone": "m3",
        "mode": "live_controller",
        "run_id": args.run_id,
        "controller": controller.name,
        "manifest": str(args.manifest),
        "model": args.model,
        "base_url": args.base_url,
        "time_scale": args.time_scale,
        "actions": actions,
        "scenarios": scenario_results,
    }
    report_path = args.out / f"live_controller_summary_{args.run_id}_{controller.name}.json"
    write_json(report_path, report)
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
