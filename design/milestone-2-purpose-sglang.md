# Milestone 2 Purpose: SGLang Gateway Router Benchmark

## Why Milestone 2 Exists

Milestone 0 proved that InferenceOps can serve a real model with a production-oriented backend.

Milestone 1 proved that InferenceOps can generate deterministic traces and replay them against an OpenAI-compatible endpoint.

Milestone 2 changes the benchmark target from a single model server to a **serving router**.

The new question is:

> Given the same workload, does the router make better or worse serving decisions?

Instead of this:

```text
trace replay -> vLLM server
```

Milestone 2 becomes this:

```text
trace replay -> SGLang Model Gateway -> worker 1
                                      -> worker 2
```

That matters because real production serving is rarely just one model process. Production systems usually need multiple workers, routing policies, health checks, retries, load balancing, and some way to preserve cache locality.

## What SGLang Is

SGLang is an open-source serving framework for large language models and vision-language models. It can launch model servers and expose OpenAI-compatible APIs, which means clients can call familiar endpoints such as chat completions without needing a custom protocol.

For InferenceOps, SGLang matters in two layers:

1. **SGLang runtime**
   - Runs model workers.
   - Serves requests through OpenAI-compatible APIs.
   - Provides high-performance LLM serving features.

2. **SGLang Model Gateway**
   - Sits in front of one or more workers.
   - Routes incoming requests to workers.
   - Supports routing policies such as cache-aware routing and load-balancing policies.
   - Can route to SGLang workers and, according to the docs, to any OpenAI-compatible backend.

The gateway is the part we care about most in Milestone 2.

## What The Gateway Does

The SGLang Model Gateway is a model-routing gateway for larger LLM deployments. Its job is to receive requests, choose a worker, forward the request, and expose operational behavior we can benchmark.

Important capabilities for InferenceOps:

| Capability | Why It Matters |
|---|---|
| Multi-worker routing | Lets us compare routing decisions across two or more model workers |
| OpenAI-compatible API surface | Lets our existing Milestone 1 replay client call the gateway with minimal changes |
| Cache-aware routing | Lets us test whether repeated prefixes benefit from being sent to the same worker |
| Load balancing | Lets us compare round-robin/random/queue-aware/cache-aware behavior |
| Health and failure handling | Lets us test degraded or failed worker scenarios |
| Metrics | Lets us capture router behavior instead of only client-side latency |

The key concept is **KV cache locality**. LLM serving workers often keep key/value cache state for recent prefixes. If many requests share the same prompt prefix, routing those requests to the same worker can avoid repeated prefill work. But always chasing cache locality can overload one worker. A good router balances both:

- cache reuse
- queue length
- worker health
- request latency

That tradeoff is exactly what InferenceOps should benchmark.

## Why Not Keep Using Only vLLM?

vLLM is still important. It gave us the first production-serving baseline.

But Milestone 2 is not primarily about raw model-serving speed. It is about **control decisions around serving**. A single vLLM endpoint cannot tell us whether a router:

- chose the right worker
- kept hot prefixes together
- avoided a slow worker
- recovered from a failed worker
- traded cache locality against queue pressure correctly

SGLang Gateway gives us a real router surface to evaluate those questions.

## What We Will Build

Milestone 2 should add:

1. **SGLang deployment scripts**
   - Start worker 1 on one port.
   - Start worker 2 on another port.
   - Start SGLang Model Gateway in front of both workers.

2. **Gateway replay path**
   - Reuse `replay/replay_trace_pack.py`.
   - Point replay at the gateway instead of a single vLLM server.

3. **Policy matrix**
   - Run the same trace pack under different routing policies.
   - Start with the smallest useful policy set:
     - `round_robin`
     - `random`
     - `power_of_two` or shortest-queue style routing, if available in the chosen gateway mode
     - `cache_aware`

4. **Router artifact format**
   - Save per-run metadata:
     - gateway policy
     - worker ports
     - model
     - GPU type
     - trace hash
     - request count
   - Save replay summaries.
   - Save gateway/worker logs.
   - Save any gateway metrics we can collect.

5. **Milestone 2 report**
   - Compare scenario/policy results in a table.
   - Identify where cache-aware routing helps or hurts.
   - Identify whether a degraded worker scenario produces visible routing/failure effects.

## First Benchmark Shape

The first benchmark should use the existing trace pack:

| Scenario | Purpose |
|---|---|
| `shared_prefix_burst` | Tests whether cache-aware routing helps repeated-prefix traffic |
| `mixed_short_long` | Tests whether routing handles short and long requests without hurting short requests |
| `degraded_worker` | Tests whether the gateway can avoid or recover from a problematic worker |

The first report should look roughly like this:

| Scenario | Policy | Requests | Failed | Latency p50 | Latency p95 | Latency p99 |
|---|---|---:|---:|---:|---:|---:|
| `shared_prefix_burst` | `round_robin` | 48 | 0 | TBD | TBD | TBD |
| `shared_prefix_burst` | `cache_aware` | 48 | 0 | TBD | TBD | TBD |
| `mixed_short_long` | `round_robin` | 48 | 0 | TBD | TBD | TBD |
| `mixed_short_long` | `cache_aware` | 48 | 0 | TBD | TBD | TBD |
| `degraded_worker` | `round_robin` | 48 | TBD | TBD | TBD | TBD |
| `degraded_worker` | health-aware/cache-aware policy | 48 | TBD | TBD | TBD | TBD |

## Done Means

Milestone 2 is complete when:

- Two real model workers are running.
- One SGLang Model Gateway fronts them.
- `traces/pack_v1` can replay through the gateway.
- At least two routing policies are compared.
- The run produces normalized replay summaries and router/worker logs.
- The Milestone 2 report explains whether routing policy changed observed behavior.

## Risks And Constraints

| Risk | Mitigation |
|---|---|
| Two workers may require more VRAM | Start with `Qwen/Qwen2.5-0.5B-Instruct` if needed |
| Gateway CLI/options may differ by SGLang version | Pin commands after first successful Lambda run |
| Cache-aware wins may be subtle on small traces | Keep the first result honest, then expand traces if needed |
| Degraded-worker simulation may need custom injection | Start with manual worker stop/slowdown before building complex fault injection |
| GPU credits can burn quickly | Build scripts locally, then run one short Lambda session |

## Reading Links

- SGLang site: https://www.sglang.io/
- SGLang docs: https://docs.sglang.io/
- SGLang Model Gateway docs: https://docs.sglang.io/advanced_features/sgl_model_gateway.html
- SGLang launch server docs: https://docs.sglang.io/backend/server_arguments.html

