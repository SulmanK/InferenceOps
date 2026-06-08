# Milestone 5: vLLM Production Stack on k3s

This runbook deploys vLLM Production Stack on a single Lambda GPU VM running k3s.

The goal is production-style Kubernetes deployment practice: k3s, Helm, NVIDIA GPU scheduling, Kubernetes Services, logs, and replay artifacts.

## References

- vLLM Production Stack docs: https://docs.vllm.ai/en/stable/deployment/integrations/production-stack/
- vLLM Production Stack repo: https://github.com/vllm-project/production-stack
- k3s NVIDIA runtime docs: https://docs.k3s.io/advanced#nvidia-container-runtime
- NVIDIA device plugin: https://github.com/NVIDIA/k8s-device-plugin

## Run Sequence

On a fresh Lambda GPU VM, copy this repo to `~/InferenceOps`, then run:

```bash
cd ~/InferenceOps
bash deploy/k3s-vllm-stack/m5_00_preflight.sh
bash deploy/k3s-vllm-stack/m5_01_install_k3s_gpu.sh
bash deploy/k3s-vllm-stack/m5_02_install_helm_device_plugin.sh
bash deploy/k3s-vllm-stack/m5_03_validate_gpu_pod.sh
bash deploy/k3s-vllm-stack/m5_04_install_vllm_stack.sh
bash deploy/k3s-vllm-stack/m5_05_port_forward.sh
bash deploy/k3s-vllm-stack/m5_06_replay_trace_pack.sh
bash deploy/k3s-vllm-stack/m5_07_collect_state.sh
```

Teardown the vLLM stack when artifacts are collected:

```bash
bash deploy/k3s-vllm-stack/m5_08_teardown_vllm_stack.sh
```

Then terminate the Lambda instance.

## Defaults

| Variable | Default |
|---|---|
| `MODEL` | `Qwen/Qwen2.5-0.5B-Instruct` |
| `VALUES_FILE` | `deploy/k3s-vllm-stack/values-qwen-0.5b.yaml` |
| `RELEASE` | `vllm` |
| `NAMESPACE` | `default` |
| `LOCAL_PORT` | `30080` |
| `TRACE_MANIFEST` | `traces/pack_v1/manifest.json` |
| `OUT_DIR` | `artifacts/m5/replay` |

## Expected Checks

```bash
sudo k3s kubectl get nodes
sudo k3s kubectl get pods -A
sudo k3s kubectl get svc
curl http://127.0.0.1:30080/v1/models
```

## Artifact Paths

```text
artifacts/m5/
artifacts/m5/replay/
artifacts/m5/k8s/
logs/m5_port_forward.log
```

Copy artifacts back after the run:

```powershell
scp -i "C:\Users\sulma\Downloads\lambda\InferenceOPS.pem" -r ubuntu@<ip>:~/InferenceOps/artifacts/m5 .\artifacts\
```
