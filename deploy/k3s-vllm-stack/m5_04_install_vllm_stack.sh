#!/usr/bin/env bash
set -euo pipefail

RELEASE="${RELEASE:-vllm}"
NAMESPACE="${NAMESPACE:-default}"
VALUES_FILE="${VALUES_FILE:-deploy/k3s-vllm-stack/values-qwen-0.5b.yaml}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m5 logs

if [ ! -f "${VALUES_FILE}" ]; then
  echo "missing values file: ${VALUES_FILE}"
  exit 1
fi

helm repo add vllm https://vllm-project.github.io/production-stack
helm repo update

helm --kubeconfig "${KUBECONFIG}" upgrade --install "${RELEASE}" vllm/vllm-stack \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  -f "${VALUES_FILE}"

helm --kubeconfig "${KUBECONFIG}" get values "${RELEASE}" -n "${NAMESPACE}" | tee "artifacts/m5/${RELEASE}_helm_values_applied.yaml"
sudo k3s kubectl get pods -n "${NAMESPACE}" -o wide | tee "artifacts/m5/${RELEASE}_pods_after_install.txt"
sudo k3s kubectl get svc -n "${NAMESPACE}" -o wide | tee "artifacts/m5/${RELEASE}_services_after_install.txt"

echo "Waiting for vLLM pods. This can take several minutes while images and model weights download."
sudo k3s kubectl wait --for=condition=Ready pod -n "${NAMESPACE}" -l "app.kubernetes.io/instance=${RELEASE}" --timeout=1200s
sudo k3s kubectl get pods -n "${NAMESPACE}" -o wide | tee "artifacts/m5/${RELEASE}_pods_ready_check.txt"

echo "vLLM Production Stack install command complete"
