#!/usr/bin/env python3
"""Create a normalized Milestone 0 summary from vLLM benchmark artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any


SUMMARY_KEYS = {
    "completed": ("completed", "num_completed_requests", "successful_requests"),
    "total_input_tokens": ("total_input_tokens", "input_tokens"),
    "total_output_tokens": ("total_output_tokens", "output_tokens"),
    "request_throughput": ("request_throughput", "requests_per_second", "req_s"),
    "output_throughput": ("output_throughput", "output_tokens_per_second", "output_tok_s"),
    "total_token_throughput": ("total_token_throughput", "total_tokens_per_second", "total_tok_s"),
    "mean_ttft_ms": ("mean_ttft_ms", "mean_ttft"),
    "median_ttft_ms": ("median_ttft_ms", "median_ttft"),
    "p95_ttft_ms": ("p95_ttft_ms", "ttft_p95_ms", "percentile_ttft_95"),
    "p99_ttft_ms": ("p99_ttft_ms", "ttft_p99_ms", "percentile_ttft_99"),
    "mean_tpot_ms": ("mean_tpot_ms", "mean_tpot"),
    "median_tpot_ms": ("median_tpot_ms", "median_tpot"),
    "p95_tpot_ms": ("p95_tpot_ms", "tpot_p95_ms", "percentile_tpot_95"),
    "p99_tpot_ms": ("p99_tpot_ms", "tpot_p99_ms", "percentile_tpot_99"),
    "mean_itl_ms": ("mean_itl_ms", "mean_itl"),
    "p95_itl_ms": ("p95_itl_ms", "itl_p95_ms", "percentile_itl_95"),
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_json(result_dir: Path, run_id: str | None) -> Path | None:
    candidates = []
    for path in result_dir.glob("*.json"):
        name = path.name.lower()
        if name.startswith(("summary_", "metadata_", "models_")):
            continue
        if run_id and run_id not in path.name:
            # vLLM does not always include our run id in generated filenames, so do not
            # reject all files solely on this condition. Prefer matching files later.
            pass
        candidates.append(path)

    if not candidates:
        return None

    matching = [p for p in candidates if run_id and run_id in p.name]
    pool = matching or candidates
    return max(pool, key=lambda p: p.stat().st_mtime)


def first_present(data: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in data:
            return data[name]
    return None


def flatten_candidate(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        if "summary" in data and isinstance(data["summary"], dict):
            merged = dict(data)
            merged.update(data["summary"])
            return merged
        return data
    return {}


def summarize_gpu_csv(result_dir: Path, run_id: str | None) -> dict[str, Any]:
    csvs = sorted(result_dir.glob("nvidia_smi*.csv"), key=lambda p: p.stat().st_mtime)
    if run_id:
        matching = [p for p in csvs if run_id in p.name]
        csvs = matching or csvs
    if not csvs:
        return {}

    path = csvs[-1]
    gpu_utils: list[float] = []
    mem_used: list[float] = []
    power: list[float] = []

    def parse_number(value: str) -> float | None:
        cleaned = value.replace("%", "").replace("MiB", "").replace("W", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, target in (
                ("utilization.gpu [%]", gpu_utils),
                ("memory.used [MiB]", mem_used),
                ("power.draw [W]", power),
            ):
                if key in row:
                    parsed = parse_number(row[key])
                    if parsed is not None:
                        target.append(parsed)

    out: dict[str, Any] = {"gpu_telemetry_file": str(path)}
    if gpu_utils:
        out["gpu_util_avg_pct"] = round(mean(gpu_utils), 3)
        out["gpu_util_max_pct"] = max(gpu_utils)
    if mem_used:
        out["gpu_memory_used_max_mib"] = max(mem_used)
    if power:
        out["gpu_power_avg_w"] = round(mean(power), 3)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    result_dir: Path = args.result_dir
    result_dir.mkdir(parents=True, exist_ok=True)

    benchmark_file = find_latest_json(result_dir, args.run_id)
    benchmark_data = flatten_candidate(load_json(benchmark_file)) if benchmark_file else {}

    summary: dict[str, Any] = {
        "milestone": "m0",
        "benchmark_file": str(benchmark_file) if benchmark_file else None,
    }

    metadata_files = sorted(result_dir.glob("metadata_*.json"), key=lambda p: p.stat().st_mtime)
    if args.run_id:
        metadata_files = [p for p in metadata_files if args.run_id in p.name] or metadata_files
    if metadata_files:
        summary["metadata"] = load_json(metadata_files[-1])

    for normalized, source_names in SUMMARY_KEYS.items():
        value = first_present(benchmark_data, source_names)
        if value is not None:
            summary[normalized] = value

    summary.update(summarize_gpu_csv(result_dir, args.run_id))

    suffix = args.run_id or "latest"
    out_path = result_dir / f"summary_{suffix}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

