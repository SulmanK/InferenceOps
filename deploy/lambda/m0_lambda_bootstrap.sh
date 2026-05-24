#!/usr/bin/env bash
set -euo pipefail

echo "InferenceOps Milestone 0 Lambda bootstrap"
echo

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is missing. This does not look like a ready Lambda GPU instance."
  exit 1
fi

nvidia-smi

if ! command -v uv >/dev/null 2>&1; then
  echo
  echo "Installing uv for the current user"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

bash deploy/vllm/m0_wsl_preflight.sh
bash deploy/vllm/m0_setup_vllm.sh

echo
echo "Lambda bootstrap complete."
echo "Next: run bash deploy/vllm/m0_serve_vllm.sh"

