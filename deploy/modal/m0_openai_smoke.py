#!/usr/bin/env python3
"""Small OpenAI-compatible smoke test for the Modal vLLM endpoint."""

from __future__ import annotations

import argparse
import json
import time

from openai import OpenAI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Modal app URL, without /v1")
    parser.add_argument("--api-key", default="local-dev")
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--prompt", default="In one paragraph, explain what TTFT measures.")
    args = parser.parse_args()

    client = OpenAI(base_url=f"{args.base_url.rstrip('/')}/v1", api_key=args.api_key)

    print("Models:")
    print(json.dumps(client.models.list().model_dump(), indent=2)[:2000])

    started = time.perf_counter()
    first_chunk_at: float | None = None
    output = []

    stream = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
        max_tokens=96,
        temperature=0,
        stream=True,
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            if first_chunk_at is None:
                first_chunk_at = time.perf_counter()
            output.append(content)
            print(content, end="", flush=True)
    print()

    finished = time.perf_counter()
    ttft = None if first_chunk_at is None else first_chunk_at - started
    print(json.dumps({
        "ttft_seconds": ttft,
        "e2e_seconds": finished - started,
        "output_chars": len("".join(output)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

