#!/usr/bin/env bash
set -euo pipefail

K3S_URL="${K3S_URL:?set K3S_URL, for example https://<server-ip>:6443}"
K3S_TOKEN="${K3S_TOKEN:?set K3S_TOKEN from the server node token}"
WORKER_PRIVATE_IP="${WORKER_PRIVATE_IP:-}"
WORKER_PUBLIC_IP="${WORKER_PUBLIC_IP:-}"
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

agent_args=()
if [ -n "${WORKER_PRIVATE_IP}" ]; then
  agent_args+=(--node-ip "${WORKER_PRIVATE_IP}")
fi

if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL="${K3S_INSTALL_CHANNEL}" K3S_URL="${K3S_URL}" K3S_TOKEN="${K3S_TOKEN}" sh -s - agent "${agent_args[@]}"
else
  echo "k3s already installed"
fi

sudo systemctl restart k3s-agent
echo "worker setup complete"
