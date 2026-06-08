# Milestone 5 Execution Plan: vLLM Production Stack on k3s

## Purpose

Milestone 5 adds production-style Kubernetes deployment experience to InferenceOps while keeping scope controlled. The target is a single Lambda GPU VM running k3s, NVIDIA GPU support, and vLLM Production Stack.

This milestone is about MLOps/platform credibility, not maximizing benchmark performance.

## Chosen Track

Use vLLM Production Stack on single-node k3s.

Reasons:

- vLLM has strong industry demand.
- Kubernetes, Helm, GPU scheduling, Services, logs, and metrics are directly relevant to MLOps roles.
- k3s keeps cost and setup complexity much lower than a full managed cluster.
- The project already has vLLM baseline and replay artifacts, so this track connects cleanly to earlier milestones.

## Non-Goals

- No managed Kubernetes yet.
- No multi-node autoscaling.
- No service mesh.
- No Terraform.
- No private networking or IAM-heavy setup.
- No Dynamo, Ray Serve, or prefill/decode disaggregation in this milestone.

## Target Topology

```text
Lambda GPU VM
  -> k3s
  -> NVIDIA device plugin / container runtime
  -> vLLM Production Stack
  -> Kubernetes Service
  -> replay_trace_pack.py
```

## Proposed Model

Default:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Fallback if resources allow:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

Use the smaller model first because Milestone 5 validates deployment mechanics.

## Done Means

- k3s is installed on one GPU VM.
- `kubectl` can see the node.
- A Kubernetes pod can see the NVIDIA GPU.
- vLLM Production Stack is installed with a documented command path.
- The model endpoint responds through a Kubernetes Service.
- `traces/pack_v1` replay completes.
- Metrics/log collection path is documented.
- Artifacts are copied back locally.
- A recap explains setup friction, cost, and how this compares to Milestone 0 and Milestone 2.

## Suggested Run Sequence

On the VM:

```bash
# 1. Install k3s
# 2. Configure NVIDIA container runtime support
# 3. Install NVIDIA device plugin
# 4. Install Helm
# 5. Install vLLM Production Stack
# 6. Wait for pods
# 7. Port-forward or expose service
# 8. Replay trace pack
```

From local workspace after the run:

```bash
scp -r ubuntu@<ip>:~/InferenceOps/artifacts/m5 ./artifacts/
```

## Acceptance Checks

- `kubectl get nodes` shows one Ready node.
- `kubectl get pods` shows vLLM serving pod Ready.
- A GPU validation pod can run `nvidia-smi`.
- `/v1/models` responds.
- Replay summaries show request count, failure count, and p95 latency.
- The runbook is specific enough to repeat on a fresh Lambda VM.

## Cost Guardrails

- Use a single GPU VM.
- Prefer H100 only if cheaper/similarly available through credits; A10/A100 is enough for deployment validation.
- Stop serving pods and terminate the instance after artifact collection.
- Do not create a managed Kubernetes cluster during Milestone 5.

