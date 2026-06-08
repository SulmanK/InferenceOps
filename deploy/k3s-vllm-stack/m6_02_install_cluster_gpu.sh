#!/usr/bin/env bash
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m6 logs

if ! command -v helm >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

for node in $(sudo k3s kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'); do
  sudo k3s kubectl label node "${node}" nvidia.com/gpu.present=true --overwrite
  sudo k3s kubectl label node "${node}" feature.node.kubernetes.io/pci-10de.present=true --overwrite
done

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
helm --kubeconfig "${KUBECONFIG}" upgrade --install nvidia-device-plugin nvdp/nvidia-device-plugin \
  --namespace nvidia-device-plugin \
  --create-namespace \
  --set runtimeClassName=nvidia

sudo k3s kubectl rollout status daemonset/nvidia-device-plugin -n nvidia-device-plugin --timeout=300s
sudo k3s kubectl get nodes -o wide | tee artifacts/m6/nodes_after_device_plugin.txt
sudo k3s kubectl describe nodes | tee artifacts/m6/nodes_describe_after_device_plugin.txt
sudo k3s kubectl get pods -A -o wide | tee artifacts/m6/pods_after_device_plugin.txt

echo "cluster gpu setup complete"
