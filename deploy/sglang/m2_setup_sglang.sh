#!/usr/bin/env bash
set -euo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi is missing. Run this on a GPU instance."
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv for the current user"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if [ ! -d .venv ]; then
  uv venv --python "${PYTHON_VERSION}" --seed
fi
source .venv/bin/activate

uv pip install sglang sglang-router openai pandas psutil pynvml

python - <<'PY'
import importlib.util
missing = [
    name for name in ("sglang", "sglang_router")
    if importlib.util.find_spec(name) is None
]
if missing:
    raise SystemExit(f"missing required modules: {', '.join(missing)}")
print("SGLang and SGLang router modules are importable.")
PY

mkdir -p artifacts/m2/replay logs

echo "Milestone 2 SGLang environment ready."
