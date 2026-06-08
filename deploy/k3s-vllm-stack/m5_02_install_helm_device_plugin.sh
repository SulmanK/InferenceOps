#!/usr/bin/env bash
set -euo pipefail

export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
mkdir -p artifacts/m5 logs

if ! command -v helm >/dev/null 2>&1; then
  echo "Installing Helm"
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

echo "Installing NVIDIA device plugin"
NODE_NAME="$(sudo k3s kubectl get nodes -o jsonpath='{.items[0].metadata.name}')"
sudo k3s kubectl label node "${NODE_NAME}" nvidia.com/gpu.present=true --overwrite
sudo k3s kubectl label node "${NODE_NAME}" feature.node.kubernetes.io/pci-10de.present=true --overwrite

helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
helm --kubeconfig "${KUBECONFIG}" upgrade --install nvidia-device-plugin nvdp/nvidia-device-plugin \
  --namespace nvidia-device-plugin \
  --create-namespace \
  --set runtimeClassName=nvidia

sudo k3s kubectl rollout status daemonset/nvidia-device-plugin -n nvidia-device-plugin --timeout=180s
sudo k3s kubectl get pods -A -o wide | tee artifacts/m5/k8s_pods_after_device_plugin.txt
sudo k3s kubectl describe node | tee artifacts/m5/k8s_node_describe_after_device_plugin.txt

echo "helm and device plugin install complete"
