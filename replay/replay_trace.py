#!/usr/bin/env python3
"""Replay an InferenceOps trace against an OpenAI-compatible chat endpoint."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from trace_schema import read_jsonl, trace_hash, validate_trace
except ImportError:  # pragma: no cover - package import path.
    from replay.trace_schema import read_jsonl, trace_hash, validate_trace


def post_json(url: str, api_key: str, payload: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any] | str]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(response_body)
            except json.JSONDecodeError:
                return response.status, response_body
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: dict[str, Any] | str = json.loads(response_body)
        except json.JSONDecodeError:
            parsed = response_body
        return exc.code, parsed
    except Exception as exc:  # noqa: BLE001 - this is a CLI artifact recorder.
        return 0, {"error": type(exc).__name__, "message": str(exc)}


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [r["latency_ms"] for r in results if r.get("ok")]
    output_tokens = [
        r.get("usage", {}).get("completion_tokens")
        for r in results
        if isinstance(r.get("usage"), dict) and isinstance(r.get("usage", {}).get("completion_tokens"), int)
    ]
    return {
        "requests": len(results),
        "successful": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "latency_ms_p50": percentile(latencies, 50),
        "latency_ms_p95": percentile(latencies, 95),
        "latency_ms_p99": percentile(latencies, 99),
        "latency_ms_mean": (sum(latencies) / len(latencies)) if latencies else None,
        "total_completion_tokens": sum(output_tokens),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", "local-dev"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/m1/replay"))
    parser.add_argument("--run-id", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    parser.add_argument("--time-scale", type=float, default=1.0, help="Scale trace arrival delays. Use 0 for no sleeping.")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true", help="Validate schedule and write artifacts without sending HTTP requests.")
    args = parser.parse_args()

    records = read_jsonl(args.trace)
    errors = validate_trace(records)
    if errors:
        for error in errors:
            print(error)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    endpoint = args.base_url.rstrip("/") + "/v1/chat/completions"
    start = time.perf_counter()
    previous_ts = 0
    results: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        ts_ms = record["ts_ms"]
        delay = max(0, ts_ms - previous_ts) / 1000.0 * args.time_scale
        if delay > 0:
            time.sleep(delay)
        previous_ts = ts_ms

        payload = {
            "model": args.model,
            "messages": record["messages"],
            "max_tokens": record["output_tokens_target"],
            "temperature": args.temperature,
        }

        request_start = time.perf_counter()
        if args.dry_run:
            status: int = 200
            response: dict[str, Any] | str = {
                "usage": {
                    "prompt_tokens": record["input_tokens_target"],
                    "completion_tokens": record["output_tokens_target"],
                    "total_tokens": record["input_tokens_target"] + record["output_tokens_target"],
                }
            }
        else:
            status, response = post_json(endpoint, args.api_key, payload, args.timeout)
        latency_ms = (time.perf_counter() - request_start) * 1000.0
        usage = response.get("usage", {}) if isinstance(response, dict) else {}
        results.append(
            {
                "index": index,
                "request_id": record["request_id"],
                "trace_ts_ms": ts_ms,
                "status": status,
                "ok": 200 <= status < 300,
                "latency_ms": latency_ms,
                "usage": usage,
                "error": response if not (200 <= status < 300) else None,
            }
        )
        print(f"{record['request_id']} status={status} latency_ms={latency_ms:.2f}")

    summary = summarize(results)
    summary.update(
        {
            "milestone": "m1",
            "run_id": args.run_id,
            "trace": str(args.trace),
            "trace_sha256": trace_hash(args.trace),
            "model": args.model,
            "base_url": args.base_url,
            "time_scale": args.time_scale,
            "dry_run": args.dry_run,
            "duration_s": time.perf_counter() - start,
        }
    )

    result_path = args.out / f"replay_results_{args.run_id}.jsonl"
    with result_path.open("w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, sort_keys=True))
            f.write("\n")

    summary_path = args.out / f"replay_summary_{args.run_id}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {result_path}")
    print(f"Wrote {summary_path}")
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
