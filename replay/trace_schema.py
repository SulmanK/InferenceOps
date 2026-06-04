#!/usr/bin/env python3
"""Shared trace schema helpers for InferenceOps Milestone 1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "ts_ms",
    "request_id",
    "tenant",
    "priority",
    "shared_prefix_id",
    "messages",
    "input_tokens_target",
    "output_tokens_target",
    "deadline_ms",
    "allow_defer",
    "prompt_generator",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{path}:{line_no}: trace record must be a JSON object")
            records.append(record)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            f.write("\n")


def validate_record(record: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        errors.append(f"record {index}: missing fields: {', '.join(missing)}")

    if not isinstance(record.get("ts_ms"), int) or record.get("ts_ms", -1) < 0:
        errors.append(f"record {index}: ts_ms must be a non-negative integer")
    if not isinstance(record.get("request_id"), str) or not record.get("request_id"):
        errors.append(f"record {index}: request_id must be a non-empty string")
    if not isinstance(record.get("shared_prefix_id"), str):
        errors.append(f"record {index}: shared_prefix_id must be a string")
    if record.get("priority") not in {"high", "normal", "low"}:
        errors.append(f"record {index}: priority must be high, normal, or low")
    if not isinstance(record.get("messages"), list) or not record.get("messages"):
        errors.append(f"record {index}: messages must be a non-empty list")
    else:
        for msg_index, message in enumerate(record["messages"]):
            if not isinstance(message, dict):
                errors.append(f"record {index}: messages[{msg_index}] must be an object")
                continue
            if message.get("role") not in {"system", "user", "assistant"}:
                errors.append(f"record {index}: messages[{msg_index}].role is invalid")
            if not isinstance(message.get("content"), str) or not message.get("content"):
                errors.append(f"record {index}: messages[{msg_index}].content must be non-empty")
    for field in ("input_tokens_target", "output_tokens_target", "deadline_ms"):
        if not isinstance(record.get(field), int) or record.get(field, 0) <= 0:
            errors.append(f"record {index}: {field} must be a positive integer")
    if not isinstance(record.get("allow_defer"), bool):
        errors.append(f"record {index}: allow_defer must be boolean")
    if not isinstance(record.get("prompt_generator"), dict):
        errors.append(f"record {index}: prompt_generator must be an object")

    return errors


def validate_trace(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    previous_ts = -1
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        errors.extend(validate_record(record, index))
        request_id = record.get("request_id")
        if request_id in seen_ids:
            errors.append(f"record {index}: duplicate request_id {request_id}")
        if isinstance(request_id, str):
            seen_ids.add(request_id)
        ts_ms = record.get("ts_ms")
        if isinstance(ts_ms, int):
            if ts_ms < previous_ts:
                errors.append(f"record {index}: ts_ms must be non-decreasing")
            previous_ts = ts_ms
    return errors


def trace_hash(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

