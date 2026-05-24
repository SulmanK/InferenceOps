# Milestone 0 on Modal

This guide deploys the Milestone 0 vLLM endpoint on Modal and runs a small OpenAI-compatible smoke test. Modal is not a traditional VM: you define a Python app, Modal builds the container, attaches the requested GPU, and exposes the server URL.

References used for this workflow:

- Modal vLLM example: https://modal.com/docs/examples/vllm_inference
- Modal GPU guide: https://modal.com/docs/guide/gpu
- Modal Secrets guide: https://modal.com/docs/guide/secrets

## 1. Create And Authenticate Modal

Create a Modal account, then install the CLI in your local Python environment:

```bash
python -m pip install modal
modal setup
```

`modal setup` opens an authentication flow and stores your local Modal token.

## 2. Create The API Key Secret

The deployed vLLM server is exposed as a web endpoint, so protect it with an API key. For a local-only benchmark key:

```bash
modal secret create inferenceops-vllm-api-key VLLM_API_KEY=local-dev
```

Use a stronger value if you will leave the endpoint deployed.

## 3. Pick A GPU

The default app uses `GPU_TYPE=L4`, which is a reasonable first target for Qwen 0.5B. Modal supports GPU strings such as `T4`, `L4`, `A10`, `L40S`, `A100`, `A100-40GB`, `A100-80GB`, `H100`, `H200`, and `B200`.

Recommended first run:

```text
GPU_TYPE=L4
MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
```

After the smoke test works, try:

```text
GPU_TYPE=L4 or A10
MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
```

## 4. Deploy The vLLM Server

From the repo root:

```bash
modal deploy deploy/modal/m0_vllm_modal.py
```

Modal will build the image, create cache volumes, start the app, and print a URL like:

```text
https://YOUR-WORKSPACE--inferenceops-m0-vllm-serve.modal.run
```

The first deploy can take several minutes because it builds the image and downloads model weights. Later starts should improve because the app uses Modal Volumes for Hugging Face and vLLM caches.

## 5. Get Or Reprint The App URL

If you missed the deployment URL, run:

```bash
modal run deploy/modal/m0_vllm_modal.py
```

Copy the printed URL into an environment variable:

```bash
export MODAL_VLLM_URL="https://YOUR-WORKSPACE--inferenceops-m0-vllm-serve.modal.run"
```

On PowerShell:

```powershell
$env:MODAL_VLLM_URL = "https://YOUR-WORKSPACE--inferenceops-m0-vllm-serve.modal.run"
```

## 6. Run A Smoke Test

Install the OpenAI client locally:

```bash
python -m pip install openai
```

Then run:

```bash
python deploy/modal/m0_openai_smoke.py \
  --base-url "$MODAL_VLLM_URL" \
  --api-key local-dev \
  --model Qwen/Qwen2.5-0.5B-Instruct
```

PowerShell:

```powershell
python deploy/modal/m0_openai_smoke.py `
  --base-url $env:MODAL_VLLM_URL `
  --api-key local-dev `
  --model Qwen/Qwen2.5-0.5B-Instruct
```

Success means:

- `/v1/models` responds.
- `/v1/chat/completions` streams output.
- The smoke script prints rough TTFT and E2E seconds.

## 7. Run The Milestone 0 Benchmark

The existing `deploy/vllm/m0_benchmark_vllm.sh` uses `vllm bench serve`. Use it from a Linux environment where the vLLM CLI is installed:

```bash
BASE_URL="$MODAL_VLLM_URL" \
API_KEY=local-dev \
MODEL=Qwen/Qwen2.5-0.5B-Instruct \
RESULT_DIR=artifacts/m0 \
REQUEST_RATE=1 \
NUM_PROMPTS=25 \
INPUT_LEN=256 \
OUTPUT_LEN=64 \
bash deploy/vllm/m0_benchmark_vllm.sh
```

Keep the first run small. Modal bills while the server is running and cold starts can dominate early measurements.

If the local benchmark client setup is annoying, use the smoke test first and treat `vllm bench serve` as the next step.

## 8. Shut Down When Done

Modal web endpoints can scale down after inactivity, but do not leave experimental deployments around accidentally. Check the Modal dashboard after the run and stop/delete the app if you are done.

Record the run in:

```text
design/milestone-0-run-report-template.md
```

## Troubleshooting

| Symptom | Likely fix |
|---|---|
| `modal` command missing | Run `python -m pip install modal` |
| Authentication error | Run `modal setup` again |
| 401 from vLLM endpoint | Check `VLLM_API_KEY` secret and `--api-key` value |
| Cold start takes minutes | Expected on first image/model build |
| Out of memory | Use `Qwen/Qwen2.5-0.5B-Instruct` or a larger GPU |
| Unexpected bill | Stop the deployment in the Modal dashboard |

