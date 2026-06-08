#!/usr/bin/env bash
set -euo pipefail

K3S_INSTALL_CHANNEL="${K3S_INSTALL_CHANNEL:-stable}"
KUBECONFIG_PATH="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"

mkdir -p artifacts/m5 logs

if ! command -v nvidia-container-runtime >/dev/null 2>&1; then
  echo "Installing NVIDIA container toolkit/runtime"
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends ca-certificates curl gnupg
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit nvidia-container-runtime
fi

if ! command -v k3s >/dev/null 2>&1; then
  echo "Installing k3s"
  curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL="${K3S_INSTALL_CHANNEL}" sh -s - --write-kubeconfig-mode 644
else
  echo "k3s already installed"
fi

sudo systemctl restart k3s

export KUBECONFIG="${KUBECONFIG_PATH}"
until sudo k3s kubectl get nodes >/dev/null 2>&1; do
  echo "waiting for k3s api"
  sleep 5
done

sudo k3s kubectl get nodes -o wide | tee artifacts/m5/k3s_nodes.txt

echo "Checking k3s containerd NVIDIA runtime detection"
sudo grep -n "nvidia" /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl \
  /var/lib/rancher/k3s/agent/etc/containerd/config.toml \
  2>/dev/null | tee artifacts/m5/k3s_nvidia_runtime_grep.txt || true

echo "k3s gpu base install complete"
