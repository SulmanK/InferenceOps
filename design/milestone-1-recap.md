# Milestone 1 Recap

## What We Built

Milestone 1 moved InferenceOps from fixed benchmark commands to deterministic trace generation and replay.

Added components:

- `replay/generate_trace_pack.py` for deterministic trace-pack generation.
- `replay/validate_trace.py` for JSONL schema validation.
- `replay/replay_trace.py` for replaying traces against an OpenAI-compatible chat endpoint.
- `replay/trace_schema.py` for shared schema, hashing, and validation helpers.
- `traces/pack_v1/` with three initial scenarios.
- `tests/test_trace_tools.py` for local validation.

## Trace Pack

`traces/pack_v1` contains:

| Scenario | Records | SHA256 |
|---|---:|---|
| `shared_prefix_burst` | 48 | `53b60a1de9d5ad49f03d12a54cabd11d3a8712b92d121f5dd266e05785c96b51` |
| `mixed_short_long` | 48 | `e36859f3b88791875b286b9f728dd3eb09910de42f421c33cdc8737e81af9026` |
| `degraded_worker` | 48 | `9bc48f8527ec9fd89b54a117addd5212d9791fe1a1aec72fcc60c47601a893fc` |

## Validation

Local validation passed:

```bash
python replay/validate_trace.py traces/pack_v1/shared_prefix_burst.jsonl traces/pack_v1/mixed_short_long.jsonl traces/pack_v1/degraded_worker.jsonl
python -m unittest discover -s tests
```

Dry-run replay also passed locally with 48/48 successful simulated requests.

## Real Replay Result

The first real replay ran on Lambda Cloud with an NVIDIA H100 PCIe against vLLM serving `Qwen/Qwen2.5-1.5B-Instruct`.

| Metric | Value |
|---|---:|
| Trace | `shared_prefix_burst` |
| Requests | 48 |
| Successful | 48 |
| Failed | 0 |
| Replay duration | 26.01 s |
| Latency p50 | 401.49 ms |
| Latency p95 | 439.18 ms |
| Latency p99 | 1132.82 ms |

## Full Trace-Pack Run

The full trace pack was replayed on 2026-06-04 with run ID `20260604T194800Z`.

| Scenario | Requests | Failed | Latency p50 | Latency p95 | Latency p99 |
|---|---:|---:|---:|---:|---:|
| `shared_prefix_burst` | 48 | 0 | 298.18 ms | 302.41 ms | 634.58 ms |
| `mixed_short_long` | 48 | 0 | 226.64 ms | 445.44 ms | 446.80 ms |
| `degraded_worker` | 48 | 0 | 298.90 ms | 301.65 ms | 302.27 ms |

See `design/milestone-1-run-report-20260604T194800Z.md`.

## Current Status

Milestone 1 is complete for `pack_v1`: deterministic traces can be generated, validated, and replayed against a real vLLM endpoint.

Next useful work:

- Add optional streaming replay if we want TTFT/TPOT from custom traces.
- Begin shaping Milestone 2 around SGLang Gateway and two workers.
