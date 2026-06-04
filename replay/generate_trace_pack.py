#!/usr/bin/env python3
"""Generate deterministic Milestone 1 trace packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

try:
    from trace_schema import trace_hash, write_jsonl
except ImportError:  # pragma: no cover - package import path.
    from replay.trace_schema import trace_hash, write_jsonl


DEFAULT_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
GENERATOR_VERSION = "m1_trace_generator_v1"


SYSTEM_PROMPTS = [
    "You are a concise infrastructure assistant. Answer with operationally useful detail.",
    "You are a production LLM serving assistant. Prefer concrete metrics and commands.",
    "You are an SRE assistant. Focus on symptoms, checks, and next actions.",
]

TOPICS = [
    "GPU memory pressure",
    "request queue latency",
    "KV cache locality",
    "prefill latency",
    "decode throughput",
    "worker health checks",
    "traffic bursts",
    "tenant priority",
]


def make_messages(rng: random.Random, prefix_id: str, topic: str, variant: int, long: bool = False) -> list[dict[str, str]]:
    stable_index = int(hashlib.sha256(prefix_id.encode("utf-8")).hexdigest(), 16) % len(SYSTEM_PROMPTS)
    system = SYSTEM_PROMPTS[stable_index]
    repeated_context = (
        f"Shared context {prefix_id}: this workload studies {topic}. "
        "The benchmark should preserve prompt structure so cache behavior can be reproduced. "
    )
    if long:
        repeated_context = repeated_context * 18
    else:
        repeated_context = repeated_context * 3
    user = (
        f"{repeated_context}\n"
        f"Request variant {variant}. "
        f"Explain the most likely bottleneck and one measurable next action. "
        f"Nonce {rng.randint(100000, 999999)}."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def base_record(
    *,
    ts_ms: int,
    request_id: str,
    tenant: str,
    priority: str,
    shared_prefix_id: str,
    messages: list[dict[str, str]],
    input_tokens_target: int,
    output_tokens_target: int,
    deadline_ms: int,
    seed: int,
    scenario: str,
    model: str,
) -> dict[str, Any]:
    return {
        "ts_ms": ts_ms,
        "request_id": request_id,
        "tenant": tenant,
        "priority": priority,
        "shared_prefix_id": shared_prefix_id,
        "messages": messages,
        "input_tokens_target": input_tokens_target,
        "output_tokens_target": output_tokens_target,
        "deadline_ms": deadline_ms,
        "allow_defer": priority == "low",
        "prompt_generator": {
            "name": GENERATOR_VERSION,
            "scenario": scenario,
            "seed": seed,
            "tokenizer": model,
            "model_revision": "default",
        },
    }


def shared_prefix_burst(seed: int, model: str, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    records = []
    hot_prefixes = ["hot_support_policy", "hot_billing_policy", "hot_incident_policy"]
    for i in range(count):
        prefix_id = hot_prefixes[i % len(hot_prefixes)]
        topic = TOPICS[i % len(TOPICS)]
        ts_ms = (i // 8) * 1000 + (i % 8) * 40
        records.append(
            base_record(
                ts_ms=ts_ms,
                request_id=f"shared_prefix_burst_{i:04d}",
                tenant="default",
                priority="normal",
                shared_prefix_id=prefix_id,
                messages=make_messages(rng, prefix_id, topic, i),
                input_tokens_target=512,
                output_tokens_target=128,
                deadline_ms=4000,
                seed=seed,
                scenario="shared_prefix_burst",
                model=model,
            )
        )
    return records


def mixed_short_long(seed: int, model: str, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed + 17)
    records = []
    for i in range(count):
        is_long = i % 5 == 0
        priority = "high" if not is_long and i % 7 == 0 else "normal"
        prefix_id = "long_context" if is_long else f"short_chat_{i % 4}"
        records.append(
            base_record(
                ts_ms=i * 500,
                request_id=f"mixed_short_long_{i:04d}",
                tenant="default",
                priority=priority,
                shared_prefix_id=prefix_id,
                messages=make_messages(rng, prefix_id, TOPICS[i % len(TOPICS)], i, long=is_long),
                input_tokens_target=2048 if is_long else 256,
                output_tokens_target=192 if is_long else 96,
                deadline_ms=8000 if is_long else 2500,
                seed=seed,
                scenario="mixed_short_long",
                model=model,
            )
        )
    return records


def degraded_worker(seed: int, model: str, count: int) -> list[dict[str, Any]]:
    rng = random.Random(seed + 31)
    records = []
    for i in range(count):
        priority = "low" if i % 6 == 0 else "normal"
        records.append(
            base_record(
                ts_ms=i * 450,
                request_id=f"degraded_worker_{i:04d}",
                tenant="default",
                priority=priority,
                shared_prefix_id=f"health_probe_group_{i % 3}",
                messages=make_messages(rng, f"health_probe_group_{i % 3}", "worker health checks", i),
                input_tokens_target=512,
                output_tokens_target=128,
                deadline_ms=5000,
                seed=seed,
                scenario="degraded_worker",
                model=model,
            )
        )
    return records


SCENARIOS = {
    "shared_prefix_burst": shared_prefix_burst,
    "mixed_short_long": mixed_short_long,
    "degraded_worker": degraded_worker,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("traces/pack_v1"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--scenarios", default="shared_prefix_burst,mixed_short_long,degraded_worker")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "trace_pack": args.out.name,
        "generator": GENERATOR_VERSION,
        "seed": args.seed,
        "model": args.model,
        "scenarios": [],
    }

    for scenario in [s.strip() for s in args.scenarios.split(",") if s.strip()]:
        if scenario not in SCENARIOS:
            raise SystemExit(f"unknown scenario: {scenario}")
        path = args.out / f"{scenario}.jsonl"
        records = SCENARIOS[scenario](args.seed, args.model, args.count)
        write_jsonl(path, records)
        manifest["scenarios"].append(
            {
                "name": scenario,
                "path": path.as_posix(),
                "records": len(records),
                "sha256": trace_hash(path),
            }
        )

    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote trace pack manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
