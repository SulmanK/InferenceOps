#!/usr/bin/env bash
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m5 logs

cat > artifacts/m5/gpu-validation-pod.yaml <<'YAML'
apiVersion: v1
kind: Pod
metadata:
  name: gpu-validation
spec:
  restartPolicy: Never
  runtimeClassName: nvidia
  containers:
    - name: cuda
      image: nvcr.io/nvidia/cuda:12.4.1-base-ubuntu22.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
      env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: all
        - name: NVIDIA_DRIVER_CAPABILITIES
          value: all
YAML

sudo k3s kubectl delete pod gpu-validation --ignore-not-found=true
sudo k3s kubectl apply -f artifacts/m5/gpu-validation-pod.yaml
sudo k3s kubectl wait --for=condition=Ready pod/gpu-validation --timeout=120s || true
sudo k3s kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/gpu-validation --timeout=180s
sudo k3s kubectl logs gpu-validation | tee artifacts/m5/gpu_validation_nvidia_smi.txt
sudo k3s kubectl delete pod gpu-validation --ignore-not-found=true

echo "gpu pod validation complete"
