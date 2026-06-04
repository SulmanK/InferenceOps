import tempfile
import unittest
from pathlib import Path

from replay.generate_trace_pack import shared_prefix_burst
from replay.trace_schema import read_jsonl, validate_trace, write_jsonl


class TraceToolsTest(unittest.TestCase):
    def test_generated_trace_is_valid(self):
        records = shared_prefix_burst(seed=42, model="Qwen/Qwen2.5-1.5B-Instruct", count=12)
        self.assertEqual(validate_trace(records), [])

    def test_jsonl_round_trip(self):
        records = shared_prefix_burst(seed=7, model="Qwen/Qwen2.5-1.5B-Instruct", count=3)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.jsonl"
            write_jsonl(path, records)
            self.assertEqual(read_jsonl(path), records)

    def test_duplicate_request_id_is_invalid(self):
        records = shared_prefix_burst(seed=42, model="Qwen/Qwen2.5-1.5B-Instruct", count=2)
        records[1]["request_id"] = records[0]["request_id"]
        errors = validate_trace(records)
        self.assertTrue(any("duplicate request_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

