#!/usr/bin/env python3
"""Validate one or more InferenceOps JSONL trace files."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from trace_schema import read_jsonl, trace_hash, validate_trace
except ImportError:  # pragma: no cover - package import path.
    from replay.trace_schema import read_jsonl, trace_hash, validate_trace


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.trace:
        records = read_jsonl(path)
        errors = validate_trace(records)
        if errors:
            failed = True
            print(f"{path}: invalid")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{path}: ok records={len(records)} sha256={trace_hash(path)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
