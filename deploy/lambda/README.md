# Milestone 0 on Lambda Cloud

Lambda Cloud is the recommended Milestone 0 execution target when you have Lambda credits. It provides normal Linux GPU VMs over SSH, which matches the current vLLM scripts.

## Recommended Instance

Use the cheapest available compatible single-GPU instance.

| Preference | GPU | Why |
|---|---|---|
| First choice | A10 24 GB | Enough VRAM for the default Qwen 1.5B baseline and a common inference GPU class |
| Second choice | A6000 48 GB | More memory headroom if A10 is unavailable |
| Avoid for vLLM | GTX 1060 / Pascal | Below current vLLM wheel requirements |

For the first run, do not use multi-GPU instances. Milestone 0 only needs one GPU.

## Lambda Console Steps

1. Add or confirm your SSH key in the Lambda Cloud console.
2. Launch an on-demand GPU instance:
   - GPU: `1x A10` if available, otherwise `1x A6000`.
   - Image: Lambda's default Ubuntu / Lambda Stack image.
   - Storage: default is fine for Milestone 0.
3. Wait for the instance to become ready.
4. SSH into the instance with the command shown by Lambda.

By default, Lambda allows SSH on port 22. You do not need to expose port 8000 publicly for Milestone 0 because the benchmark runs on the same VM against `127.0.0.1`.

## Repo Setup On The Instance

Clone the repo if it has a remote:

```bash
git clone <repo-url> InferenceOps
cd InferenceOps
```

If the repo is not pushed anywhere yet, copy it from your local machine:

```bash
scp -r /path/to/InferenceOps ubuntu@<lambda-ip>:~/InferenceOps
ssh ubuntu@<lambda-ip>
cd ~/InferenceOps
```

## Run Milestone 0

On the Lambda instance:

```bash
bash deploy/lambda/m0_lambda_bootstrap.sh
```

Start the vLLM server:

```bash
bash deploy/vllm/m0_serve_vllm.sh
```

In a second SSH session:

```bash
cd ~/InferenceOps
bash deploy/vllm/m0_benchmark_vllm.sh
```

## Smaller Model Fallback

If the default model is slow to load or memory is tight:

```bash
MODEL=Qwen/Qwen2.5-0.5B-Instruct bash deploy/vllm/m0_serve_vllm.sh
```

Then in the benchmark shell:

```bash
MODEL=Qwen/Qwen2.5-0.5B-Instruct bash deploy/vllm/m0_benchmark_vllm.sh
```

## Copy Artifacts Back

From your local machine:

```bash
scp -r ubuntu@<lambda-ip>:~/InferenceOps/artifacts/m0 ./artifacts/
```

Then fill in:

```text
design/milestone-0-run-report-template.md
```

## Shutdown

Terminate the Lambda instance when the benchmark artifacts are copied back. Credits still matter even when the run is small.

