# Milestone 5 Recap: vLLM Production Stack on k3s

## What Ran

Milestone 5 deployed vLLM Production Stack on a single Lambda GPU VM running k3s.

VM:

- Provider: Lambda
- OS: Ubuntu 22.04.5 LTS
- GPU: NVIDIA A100-SXM4-40GB
- Kubernetes: k3s `v1.35.5+k3s1`

Model:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Run ID:

```text
20260608T144831Z
```

## Deployment Path

The successful path was:

```text
Lambda GPU VM
  -> k3s
  -> NVIDIA container runtime
  -> NVIDIA Kubernetes device plugin
  -> vLLM Production Stack Helm chart
  -> vLLM router Kubernetes Service
  -> replay_trace_pack.py
```

## Important Fixes

Two k3s/GPU details mattered:

- The NVIDIA device plugin Helm chart required GPU-presence node labels on this single-node k3s VM.
- The device-plugin pod needed `runtimeClassName: nvidia`; otherwise it failed with `NVML: ERROR_LIBRARY_NOT_FOUND`.

The runbook scripts now handle both.

## Validation

GPU validation pod successfully ran `nvidia-smi` inside Kubernetes.

The vLLM Production Stack router responded through port-forward:

```text
http://127.0.0.1:30080/v1/models
```

The endpoint reported:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

## Replay Results

All three `traces/pack_v1` scenarios completed successfully through the Kubernetes-deployed vLLM Production Stack.

| Scenario | Requests | Failed | P50 ms | P95 ms | P99 ms | Duration s |
|---|---:|---:|---:|---:|---:|---:|
| `shared_prefix_burst` | 48 | 0 | 279.04 | 280.90 | 748.65 | 19.49 |
| `mixed_short_long` | 48 | 0 | 213.68 | 415.19 | 415.91 | 35.75 |
| `degraded_worker` | 48 | 0 | 279.71 | 280.89 | 281.74 | 34.51 |

Total:

```text
144 requests
0 failures
```

## Artifacts

Artifacts were copied locally to:

```text
C:\tmp\InferenceOps-m5
```

Remote artifact paths:

```text
artifacts/m5/
artifacts/m5/replay/
artifacts/m5/k8s/
```

Captured artifact categories:

- replay summaries and results
- k3s node descriptions
- pod and service listings
- Helm values and rendered manifests
- vLLM/router logs
- GPU validation output
- final `nvidia-smi`

## Current VM State

The vLLM Helm release was uninstalled after artifact collection.

k3s system pods and the NVIDIA device plugin remain running. No GPU compute process was listed after teardown.

Terminate the Lambda instance when finished to stop billing.

## Closeout

Milestone 5 v0 is complete.

Done:

- k3s installed on a single GPU VM.
- NVIDIA GPU scheduling works inside Kubernetes.
- vLLM Production Stack deployed via Helm.
- Model endpoint responded through a Kubernetes Service.
- Deterministic trace pack replay completed.
- Kubernetes logs, manifests, state, and replay artifacts were captured.
- Setup friction and required GPU fixes were documented.

