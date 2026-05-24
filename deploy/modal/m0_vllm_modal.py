"""Modal deployment for InferenceOps Milestone 0 vLLM serving.

Run:
    modal setup
    modal secret create inferenceops-vllm-api-key VLLM_API_KEY=local-dev
    modal deploy deploy/modal/m0_vllm_modal.py

The deployed app exposes an OpenAI-compatible vLLM server.
"""

from __future__ import annotations

import os
import subprocess

import modal


APP_NAME = "inferenceops-m0-vllm"
MODEL_NAME = os.environ.get("MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")
SERVED_MODEL_NAME = os.environ.get("SERVED_MODEL_NAME", MODEL_NAME)
GPU_TYPE = os.environ.get("GPU_TYPE", "L4")
VLLM_PORT = 8000
MINUTES = 60

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm", "openai", "aiohttp")
)

hf_cache = modal.Volume.from_name("inferenceops-huggingface-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("inferenceops-vllm-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu=GPU_TYPE,
    timeout=15 * MINUTES,
    scaledown_window=10 * MINUTES,
    secrets=[modal.Secret.from_name("inferenceops-vllm-api-key")],
    volumes={
        "/root/.cache/huggingface": hf_cache,
        "/root/.cache/vllm": vllm_cache,
    },
)
@modal.concurrent(max_inputs=50)
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve() -> None:
    api_key = os.environ["VLLM_API_KEY"]
    cmd = [
        "vllm",
        "serve",
        MODEL_NAME,
        "--served-model-name",
        SERVED_MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--dtype",
        "auto",
        "--api-key",
        api_key,
        "--uvicorn-log-level",
        "info",
    ]
    print("Starting:", " ".join(cmd), flush=True)
    subprocess.Popen(cmd)


@app.local_entrypoint()
def print_url() -> None:
    print("Deployed URL:")
    print(serve.get_web_url())

