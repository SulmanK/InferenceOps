#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it first: https://docs.astral.sh/uv/"
  exit 1
fi

uv venv --python "${PYTHON_VERSION}" --seed
source .venv/bin/activate

uv pip install --torch-backend=auto vllm openai pandas psutil pynvml

mkdir -p artifacts/m0 logs

echo "Milestone 0 vLLM environment ready."

