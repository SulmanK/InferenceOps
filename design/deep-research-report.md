# InferenceOps Deep Research Plan

## Executive Summary

InferenceOps should be a practical benchmark harness for evaluating LLM serving control policies on real serving systems. The core project is not a pure simulator and not a generic serving demo. It is a reproducible system that sends trace-defined traffic through real LLM serving backends, records latency and operational telemetry, and compares routing/control policies under cache, latency, load, and failure pressure.

The primary goals are:

- Build portfolio-quality production systems work with concrete artifacts.
- Learn practical GPU serving through real vLLM and SGLang runs.
- Keep research depth, simulator calibration, and agentic controllers available as later layers after the core harness is reproducible.

The active workspace/repo name is `InferenceOps`. This document is an internal design plan for the workspace, not a public-facing report or marketing artifact.

## Project Thesis

Modern serving stacks already expose the primitives this project needs: OpenAI-compatible request APIs, benchmark CLIs, router/gateway policies, health checks, metrics, tracing, and advanced features such as cache-aware routing, prefill/decode disaggregation, autoscaling, and shared KV cache.

The useful project layer is the control benchmark above those systems:

> A benchmark harness for evaluating serving control policies on real LLM routers under cache, latency, load, and failure pressure.

The benchmark should answer operational questions such as:

- Did the policy route requests to preserve cache locality without creating queueing tail latency?
- Did it protect short or high-priority requests from long-prefill traffic?
- Did it stop sending work to degraded or failed workers quickly enough?
- Did it improve SLO miss rate, throughput, or cost without relying on brittle one-off behavior?

## V0 Scope

V0 should be small, real, and reproducible. It should include:

- A single-backend vLLM serving baseline.
- Deterministic trace generation and replay.
- SGLang Model Gateway in front of two small workers.
- Three benchmark scenarios:
  - shared-prefix burst
  - mixed short/long workload
  - degraded worker
- Three to four policies:
  - round robin
  - power of two or shortest queue
  - cache-aware routing
  - one simple heuristic hybrid
- Normalized run artifacts.
- An internal leaderboard/report based on raw metrics.

V0 should not depend on agentic controllers, Kubernetes, Ray Serve, Dynamo, shared KV cache, autoscaling, or a calibrated simulator. Those are later milestones.

## Architecture

InferenceOps should be API-first, but "backend-agnostic" must be precise. There are two separate interfaces:

1. **Request/data plane**
   - Sends OpenAI-compatible requests where possible.
   - Measures request-level outcomes such as TTFT, TPOT, E2E latency, errors, output tokens, and status.
   - Should work across vLLM, SGLang, Ray Serve LLM, and other compatible endpoints.

2. **Control adapter plane**
   - Uses backend-specific APIs/configuration to read state and apply actions.
   - Handles policy changes, worker health, queue/load metrics, drain/resume, route overrides, and unsupported actions.
   - Must explicitly report when a backend cannot support a requested control action.

This distinction matters because OpenAI-compatible APIs are enough for replay and measurement, but they are not enough for meaningful control-policy benchmarking.

Recommended workspace structure:

| Path | Purpose |
|---|---|
| `design/` | Internal plans, benchmark specs, and architecture notes |
| `backends/` | Backend adapters and control adapters |
| `replay/` | Load generation and trace replay |
| `traces/` | Versioned workload packs |
| `controllers/` | Static, heuristic, and later agentic policies |
| `metrics/` | Normalization, summaries, plots, and report generation |
| `artifacts/` | Run outputs, raw telemetry, summaries, and leaderboards |
| `deploy/` | Launch scripts and backend configs |

## Milestone Gates

The timeline is intentionally milestone-based rather than calendar-based. Each milestone should produce artifacts that make the next milestone easier and safer.

### Milestone 0: Single-Backend vLLM Baseline

Goal: prove that the workspace can run a real LLM serving backend and capture useful benchmark artifacts.

Production serving platform: **vLLM**. It is the first backend because it is production-oriented, widely used for LLM serving, exposes an OpenAI-compatible API, and includes benchmark tooling that can seed the InferenceOps artifact format.

Done means:

- vLLM serves a small instruct model such as `Qwen/Qwen2.5-0.5B-Instruct` or `Qwen/Qwen2.5-1.5B-Instruct`.
- `/v1/models` and `/v1/chat/completions` work through the OpenAI-compatible API.
- A deterministic benchmark run records TTFT, TPOT, E2E latency, throughput, request errors, and output tokens.
- GPU telemetry is captured with run metadata.
- Artifacts include raw benchmark JSON, telemetry CSV, normalized summary JSON, and a short internal markdown report.

Recommended default:

- Start with Qwen because it has low setup friction and small models.
- Treat Llama-family models as later comparison targets after the harness is stable.
- Windows development can use WSL2, but the actual vLLM GPU run requires a compatible NVIDIA GPU. The current local WSL preflight sees a GTX 1060 with compute capability 6.1, which is below current vLLM NVIDIA wheel requirements, so Milestone 0 serving should run on a compatible cloud GPU or newer local GPU.
- Since Lambda credits are available, Lambda Cloud is the primary Milestone 0 execution target. Prefer a single `A10` instance first, with `A6000` as the fallback if A10 capacity is unavailable.

### Milestone 1: Deterministic Trace Generation and Replay

Goal: move from one-off benchmark commands to reproducible workload replay.

Status: complete for `pack_v1`. `traces/pack_v1` exists, all JSONL traces validate, and all three scenarios have been replayed successfully against a real vLLM `/v1/chat/completions` endpoint.

Done means:

- Trace packs are versioned and replayable.
- Replay preserves arrival timing, burst structure, prompt/prefix structure, target output length, priority, and request identity.
- The same trace can be replayed through the vLLM endpoint with stable artifact output.
- Run metadata records model ID, model revision, tokenizer, backend version, hardware, seed, and trace hash.

Token lengths alone are not enough for cache/locality evaluation. A trace record must include actual prompts or deterministic prompt-generation metadata.

Minimum trace record fields:

```json
{
  "ts_ms": 0,
  "request_id": "req_000001",
  "tenant": "default",
  "priority": "normal",
  "shared_prefix_id": "chat_session_17",
  "prompt": "actual prompt text or omitted only when prompt_generator is present",
  "prompt_generator": {
    "name": "shared_prefix_chat_v1",
    "seed": 42,
    "tokenizer": "Qwen/Qwen2.5-1.5B-Instruct",
    "model_revision": "recorded revision"
  },
  "input_tokens_target": 512,
  "output_tokens_target": 128,
  "deadline_ms": 4000,
  "allow_defer": true
}
```

### Milestone 2: Real Router Benchmark

Goal: benchmark routing behavior with a real router in front of real workers.

Purpose note: see `design/milestone-2-purpose-sglang.md` for the detailed explanation of why this milestone uses SGLang Model Gateway and what router behavior we want to measure.

Status: completed for v0. See `design/milestone-2-recap.md` for the SGLang Gateway run summary.

Done means:

- SGLang Model Gateway fronts two small workers.
- The replay harness can send the same trace through the gateway.
- The benchmark compares at least three built-in policies, such as round robin, power of two, and cache-aware routing.
- Worker health, queue/load, errors, and available router metrics are captured through a control adapter.
- Scenarios include shared-prefix burst, mixed short/long workload, and degraded worker.
- The internal leaderboard reports raw metrics per policy and scenario.

Milestone 2 is the first major proof point. Do not start Kubernetes, Ray Serve, Dynamo, or agentic controller work until this benchmark produces stable artifacts.

### Milestone 3: Heuristic Controllers and Policy Comparison

Goal: make control policy the benchmark target rather than only comparing built-in router modes.

Status: started. The first pass adds offline policy normalization and bounded heuristic controller evaluation over the Milestone 2 replay artifacts. See `design/milestone-3-execution-plan.md` and `design/milestone-3-recap.md`.

Done means:

- At least one heuristic hybrid policy is implemented.
- The controller observes normalized state from the control adapter.
- The controller chooses from a small finite action space.
- The policy is compared against static and built-in policies on the same scenarios.
- The report explains where the heuristic wins, where it loses, and whether the result is robust across repeated runs.

Useful initial heuristic:

- Prefer cache-aware routing for hot-prefix groups when queue pressure is low.
- Prefer queue-aware routing when queue pressure or worker degradation dominates.
- Defer or shed low-priority work only under explicit overload scenarios.

### Milestone 4: Optional Agentic Controller

Goal: evaluate whether an LLM-based controller can make useful bounded decisions after strong non-agentic baselines exist.

Done means:

- The agent has the same observation interface as other controllers.
- The action space is finite and guarded.
- Official evaluations use deterministic settings, including temperature 0.
- Invalid actions are logged and replaced by a safe fallback.
- Agentic results are compared against heuristic baselines, not just weak static baselines.

The agentic controller is not required for the first credible benchmark. If it performs worse than heuristics, that is still a valid benchmark result.

### Milestone 5: Optional Advanced Systems Track

Goal: add one advanced serving-system feature after the core benchmark is stable.

Potential tracks:

- Ray Serve LLM for distributed orchestration and observability.
- vLLM Production Stack for Kubernetes, KV-aware routing, tracing, autoscaling, or shared KV cache.
- Dynamo for disaggregation, KV-aware routing, and systems-level control-plane design.
- Prefill/decode disaggregation experiments.
- Shared KV or cache-budget experiments.

Pick one track at a time. This milestone should not become a rewrite of the core benchmark.

## Benchmark Scenarios

V0 should keep the scenario set small and clear.

| Scenario | Workload | Injection | Primary question |
|---|---|---|---|
| Shared-prefix burst | Many requests reuse hot prefixes or sessions | None | Does the policy exploit locality without increasing tail latency? |
| Mixed short/long | Short chat prompts mixed with long-context prompts | None | Can the policy protect short requests from long-prefill interference? |
| Degraded worker | Steady traffic with shared-prefix groups | One worker slowed or made error-prone | Does the policy stop feeding a bad worker quickly enough? |

Later scenarios can add failed worker, overload shedding, tenant priority, budget-aware serving, cache pollution, and prefill/decode candidates.

## Metrics and Reporting

V0 should publish raw metrics first. Do not lead with a composite score until the scenario definitions and metric normalization are stable.

Required V0 metrics:

- TTFT p50/p95/p99
- TPOT p50/p95/p99
- E2E latency p50/p95/p99
- request throughput
- output tokens/sec and total tokens/sec
- error rate
- drop/reject rate when applicable
- SLO miss rate
- cache-locality proxy
- GPU utilization and max GPU memory
- controller action count
- invalid action count

Composite leaderboard scoring can be added later as an optional derived metric. The raw metrics remain the source of truth.

## Controller Action Space

Controllers should start with a finite, safe action space.

| Action | Parameters | V0/V1 status |
|---|---|---|
| `set_policy` | `round_robin`, `power_of_two`, `cache_aware` | Allowed when backend supports it |
| `route_override` | worker ID for next request or request batch | Optional, adapter-dependent |
| `defer_low_priority` | priority band and defer duration | Allowed in overload scenarios |
| `cap_concurrency` | integer cap | Optional, adapter-dependent |
| `drain_worker` | worker ID | Allowed for health/failure scenarios |
| `resume_worker` | worker ID | Allowed after health recovery |
| `shed_load` | priority band or tenant | Allowed with explicit scenario guardrails |

Do not allow arbitrary shell commands, unrestricted Kubernetes operations, or free-form router rewrites as controller actions.

Guardrails:

- Invalid actions fall back to a safe policy.
- Known unhealthy workers must not receive traffic.
- Topology or policy changes should be rate-limited to avoid flapping.
- Controller inference must fit within a bounded control latency budget.
- Every observation, action, reason, and resulting metric window must be logged.

## Simulator Calibration

The simulator is a support tool, not the benchmark source of truth.

Use real runs to collect:

- request-level outcomes
- prompt and token features
- queue/load observations
- worker health observations
- cache-locality proxy signals
- GPU telemetry

Then fit simple models for TTFT, TPOT, drop probability, cache-locality proxy, and cost. Use the simulator for offline policy search and stress-scenario generation. Publish real backend reruns for any result that matters.

If simulator validation is weak, label it advisory only.

## Cost and Infrastructure Guidance

Cost estimates are planning guidance, not milestone drivers.

Recommended starting strategy:

- Use one cheap GPU for Milestones 0 and 1.
- Use either one larger GPU that can colocate two small workers, or two small GPU instances, for Milestone 2.
- Keep scenario packs short during development.
- Run repeated measurements only after harness bugs are fixed.
- Prefer real runs for final comparisons and simulator runs for cheap exploration.

Avoid persistent cluster work until Milestone 2 has stable artifacts.

## Internal Artifacts

Each milestone should produce evidence:

- exact run command or config
- trace hash
- backend/model/hardware metadata
- raw request-level output
- normalized summary JSON
- telemetry capture
- internal markdown report
- plots or tables for scenario comparison

The internal report should be readable and reproducible, but it does not need public-facing polish, blog framing, demo GIFs, or external marketing copy.

## Acceptance Criteria

This design plan is satisfied when:

- The active report lives at `design/deep-research-report.md`.
- The plan uses milestone gates instead of an 8-week dependency.
- Every milestone has a concrete "done means" definition.
- V0 scope is limited to the real benchmark core.
- Trace replay requirements include actual prompts or deterministic prompt-generation metadata.
- Backend-agnostic language distinguishes the request/data plane from backend-specific control adapters.
- Agentic controllers are optional and come after heuristic baselines.
- Simulator calibration is framed as support, with real backend runs as source of truth.
- Malformed citation/entity artifacts from the original research report are not present in the active design document.
