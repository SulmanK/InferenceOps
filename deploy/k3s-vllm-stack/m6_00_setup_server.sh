#!/usr/bin/env bash
set -euo pipefail

SERVER_PRIVATE_IP="${SERVER_PRIVATE_IP:-}"
SERVER_PUBLIC_IP="${SERVER_PUBLIC_IP:-}"
K3S_INSTALL_CHANNEL="${K3S_INSTALL_CHANNEL:-stable}"

mkdir -p artifacts/m6 logs

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is missing. Use a GPU image with NVIDIA drivers installed."
  exit 1
fi

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

install_args=(--write-kubeconfig-mode 644)
if [ -n "${SERVER_PRIVATE_IP}" ]; then
  install_args+=(--advertise-address "${SERVER_PRIVATE_IP}" --node-ip "${SERVER_PRIVATE_IP}" --tls-san "${SERVER_PRIVATE_IP}")
fi
if [ -n "${SERVER_PUBLIC_IP}" ]; then
  install_args+=(--tls-san "${SERVER_PUBLIC_IP}")
fi

if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL="${K3S_INSTALL_CHANNEL}" sh -s - "${install_args[@]}"
else
  echo "k3s already installed"
fi

sudo systemctl restart k3s
until sudo k3s kubectl get nodes >/dev/null 2>&1; do
  echo "waiting for k3s api"
  sleep 5
done

NODE_NAME="$(sudo k3s kubectl get nodes -o jsonpath='{.items[0].metadata.name}')"
sudo k3s kubectl label node "${NODE_NAME}" nvidia.com/gpu.present=true --overwrite
sudo k3s kubectl label node "${NODE_NAME}" feature.node.kubernetes.io/pci-10de.present=true --overwrite

sudo k3s kubectl get nodes -o wide | tee artifacts/m6/server_nodes.txt
sudo cat /var/lib/rancher/k3s/server/node-token | tee artifacts/m6/server_node_token.txt >/dev/null

echo "server setup complete"
echo "server token saved to artifacts/m6/server_node_token.txt"
