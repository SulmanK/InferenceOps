#!/usr/bin/env bash
set -euo pipefail

RELEASE="${RELEASE:-vllm}"
NAMESPACE="${NAMESPACE:-default}"

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m6/k8s logs

sudo k3s kubectl get nodes -o wide > artifacts/m6/k8s/nodes.txt
sudo k3s kubectl describe nodes > artifacts/m6/k8s/nodes_describe.txt
sudo k3s kubectl get pods -A -o wide > artifacts/m6/k8s/pods_all.txt
sudo k3s kubectl get svc -A -o wide > artifacts/m6/k8s/services_all.txt
helm --kubeconfig "${KUBECONFIG}" list -A > artifacts/m6/k8s/helm_list.txt
helm --kubeconfig "${KUBECONFIG}" get values "${RELEASE}" -n "${NAMESPACE}" > "artifacts/m6/k8s/${RELEASE}_helm_values.yaml" || true
helm --kubeconfig "${KUBECONFIG}" get manifest "${RELEASE}" -n "${NAMESPACE}" > "artifacts/m6/k8s/${RELEASE}_helm_manifest.yaml" || true

for pod in $(sudo k3s kubectl get pods -n "${NAMESPACE}" -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep -E 'vllm|router' || true); do
  sudo k3s kubectl logs -n "${NAMESPACE}" "${pod}" --all-containers=true > "artifacts/m6/k8s/log_${pod}.txt" || true
done

nvidia-smi > artifacts/m6/k8s/nvidia_smi_server_final.txt
echo "Milestone 6 state collected under artifacts/m6/k8s"
