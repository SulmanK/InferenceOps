# Milestone 6 Execution Plan: vLLM Production Stack Scaling Experiment

## Purpose

Milestone 6 demonstrates an industry-style scaling path for the serving stack.

Milestone 5 proved that vLLM Production Stack can run on one GPU VM with k3s. Milestone 6 asks the more production-relevant question:

```text
What changes when the stack runs multiple serving replicas across multiple GPU nodes?
```

This is stronger than a simple managed-Kubernetes portability check because it evaluates routing, load distribution, throughput, latency, utilization, and cost under higher load.

## Target Architecture

Preferred Option C:

```text
2 Lambda GPU VMs
  -> one k3s server/control-plane node
  -> one k3s agent/worker node
  -> NVIDIA runtime + device plugin on both nodes
  -> vLLM Production Stack Helm deployment
  -> 2 vLLM serving replicas
  -> vLLM router Kubernetes Service
  -> high-pressure trace replay
```

The same model should run on both serving replicas.

Default model:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Fallback model if scheduling or memory becomes tight:

```text
facebook/opt-125m
```

## Why This Is Industry-Relevant

This mirrors the core pattern used in production inference stacks:

- Kubernetes schedules GPU-backed serving pods.
- A router/service hides backend replicas from clients.
- Replicas can be added for capacity.
- Operators compare cost, throughput, tail latency, and utilization.
- Bottlenecks are diagnosed through pod state, router logs, GPU metrics, and replay results.

This is more valuable than simply proving the manifests can run on another provider.

## Experiment Design

Run A: single-replica baseline

- one serving replica
- one GPU node active for serving
- replay `traces/pack_v1`
- run higher-pressure replay variants

Run B: two-replica scaling run

- two serving replicas
- two GPU nodes schedulable
- route through the same vLLM router
- replay the same workloads with the same settings

Compare Run B against Run A.

## Load Plan

Use at least two load levels:

| Load Level | Method | Purpose |
|---|---|---|
| normal | `TIME_SCALE=1.0` | compare to Milestone 5 |
| pressure | `TIME_SCALE=0.25` or concurrent replay clients | expose throughput and tail-latency behavior |

If time allows, add a heavier trace pack later. Do not block Milestone 6 on new trace generation.

## Metrics

Required:

- total requests
- failures
- p50/p95/p99 end-to-end latency
- request throughput
- output token throughput if available
- run duration
- GPU utilization per node
- max GPU memory per node
- pod readiness/restarts
- router logs
- cost estimate per run

Optional:

- per-replica request distribution from router logs or metrics
- Prometheus/Grafana screenshots if the stack exposes them cleanly
- p95 latency per scenario under normal vs pressure load

## Done Means

- Two GPU VMs are joined into one k3s cluster.
- Both nodes advertise `nvidia.com/gpu`.
- vLLM Production Stack deploys two serving replicas.
- The router service responds to `/v1/models`.
- Normal and pressure replay runs complete through the router.
- Artifacts are collected for both baseline and scaling runs.
- The recap compares one-replica vs two-replica behavior.
- The recap identifies bottlenecks and whether the extra GPU node improved useful capacity.

## Non-Goals

- No managed Kubernetes provider unless Lambda/k3s cannot support the experiment.
- No multi-region setup.
- No service mesh.
- No Terraform.
- No private networking design beyond what is needed for the two nodes to join.
- No autoscaling controller in v0; use fixed replica counts first.

## Cluster Setup Strategy

Use k3s multi-node:

- Node 1: k3s server/control-plane.
- Node 2: k3s agent joined with the server token.
- Install NVIDIA runtime support on both nodes.
- Install NVIDIA device plugin once in the cluster.
- Confirm both nodes advertise `nvidia.com/gpu: 1`.

Important checks:

```bash
sudo k3s kubectl get nodes -o wide
sudo k3s kubectl describe nodes | grep -A8 "nvidia.com/gpu"
sudo k3s kubectl get pods -A -o wide
```

## Deployment Strategy

Use the Milestone 5 values file as the base, then create a two-replica values file:

```yaml
servingEngineSpec:
  runtimeClassName: "nvidia"
  modelSpec:
    - name: "qwen05b"
      modelURL: "Qwen/Qwen2.5-0.5B-Instruct"
      replicaCount: 2
      requestGPU: 1
      requestGPUType: "nvidia.com/gpu"
```

The expected scheduling outcome is one serving pod per GPU node.

## Acceptance Checks

- `kubectl get nodes` shows two Ready nodes.
- `kubectl describe nodes` shows one GPU allocatable on each node.
- `kubectl get pods -o wide` shows two vLLM serving pods on different nodes.
- Router pod is Ready.
- `/v1/models` responds through port-forward.
- `traces/pack_v1` replay completes at normal and pressure settings.
- The two-replica run is compared against the one-replica baseline.

## Risk Notes

- Lambda may require private networking/firewall configuration for the k3s agent to join the server.
- If two nodes cannot join cleanly, stop and document the blocker rather than burning credits.
- If two replicas cannot fit with Qwen 0.5B due to image/runtime behavior, use `facebook/opt-125m` to validate scaling mechanics.
- If router logs do not expose request distribution clearly, use pod logs and GPU telemetry as the first-pass distribution proxy.

## Cost Guardrails

- Keep the cluster alive only for the experiment window.
- Start with the smallest available GPU type that can run the chosen model.
- Run one baseline and one scaling pass before adding variants.
- Tear down Helm releases and terminate both VMs after artifact collection.

## Output

Create `design/milestone-6-recap.md` with:

- cluster topology
- instance types
- setup steps and friction
- one-replica baseline table
- two-replica scaling table
- pressure-load comparison
- GPU utilization summary
- cost estimate
- bottleneck analysis
- whether the result supports the scaling story
