# Milestone 1 Full Trace-Pack Run Report

## Run Metadata

| Field | Value |
|---|---|
| Run ID | `20260604T194800Z` |
| Date | 2026-06-04 |
| Milestone | M1 deterministic trace-pack replay |
| Cloud/provider | Lambda Cloud |
| GPU | NVIDIA H100 80GB HBM3 |
| Driver/CUDA | NVIDIA driver 580.105.08, CUDA 13.0 |
| Backend | vLLM 0.22.0 |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Endpoint | `http://127.0.0.1:8000/v1/chat/completions` |
| Trace pack | `traces/pack_v1/manifest.json` |
| Time scale | 1.0 |

## Results

| Scenario | Requests | Failed | Duration | Latency p50 | Latency p95 | Latency p99 | Completion tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| `shared_prefix_burst` | 48 | 0 | 20.22 s | 298.18 ms | 302.41 ms | 634.58 ms | 6131 |
| `mixed_short_long` | 48 | 0 | 36.57 s | 226.64 ms | 445.44 ms | 446.80 ms | 5568 |
| `degraded_worker` | 48 | 0 | 35.52 s | 298.90 ms | 301.65 ms | 302.27 ms | 6144 |

## Artifact Paths

| Artifact | Path |
|---|---|
| Batch summary | `artifacts/m1/replay/trace_pack_replay_summary_20260604T194800Z.json` |
| Shared-prefix summary | `artifacts/m1/replay/replay_summary_20260604T194800Z_shared_prefix_burst.json` |
| Mixed short/long summary | `artifacts/m1/replay/replay_summary_20260604T194800Z_mixed_short_long.json` |
| Degraded worker summary | `artifacts/m1/replay/replay_summary_20260604T194800Z_degraded_worker.json` |
| Shared-prefix results | `artifacts/m1/replay/replay_results_20260604T194800Z_shared_prefix_burst.jsonl` |
| Mixed short/long results | `artifacts/m1/replay/replay_results_20260604T194800Z_mixed_short_long.jsonl` |
| Degraded worker results | `artifacts/m1/replay/replay_results_20260604T194800Z_degraded_worker.jsonl` |
| vLLM log | `artifacts/m1/replay/vllm_20260604T194800Z.log` |

## Notes

- This run completes the Milestone 1 goal for `pack_v1`: every trace scenario generated locally was replayed successfully against a real vLLM endpoint.
- All three scenarios completed with zero failed requests.
- The current replay client records end-to-end request latency and OpenAI usage fields. Streaming TTFT/TPOT for custom traces remains optional future work.

