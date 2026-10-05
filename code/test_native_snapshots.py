"""Integrity checks for the frozen native tool schemas. Offline, no Docker."""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import hashlib
import json
import re
import unittest
from pathlib import Path

import capture_native_schemas as capture


SNAPSHOT_DIR = Path("data/source_snapshots/native")
RAW_DIR = SNAPSHOT_DIR / "raw"


def load_snapshot(key):
    return json.loads((SNAPSHOT_DIR / f"{key}.json").read_text(encoding="utf-8"))


class NativeSnapshotTests(unittest.TestCase):
    def test_every_selected_server_is_frozen(self):
        expected = sorted(server["key"] for server in capture.SERVERS)
        frozen = sorted(path.stem for path in SNAPSHOT_DIR.glob("*.json"))
        self.assertEqual(frozen, expected)
        self.assertEqual(len(expected), 8)
        tasks = sorted(server["task"] for server in capture.SERVERS)
        self.assertEqual(tasks, ["calendar"] * 2 + ["email"] * 2 + ["files"] * 2 + ["orders"] * 2)

    def test_raw_bytes_match_the_recorded_hashes(self):
        # This is what makes the capture verifiable: anyone can re-hash the raw
        # response and compare it with the value frozen at capture time.
        for server in capture.SERVERS:
            with self.subTest(server=server["key"]):
                snapshot = load_snapshot(server["key"])
                raw = (RAW_DIR / f"{server['key']}.tools_list.json").read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                self.assertEqual(digest, snapshot["source_sha256"])
                self.assertEqual([digest], snapshot["provenance"]["capture"]["tools_list_page_sha256"])
                self.assertEqual(json.loads(raw), snapshot["native_tools_list"])

    def test_provenance_matches_the_selection(self):
        for server in capture.SERVERS:
            with self.subTest(server=server["key"]):
                provenance = load_snapshot(server["key"])["provenance"]
                self.assertEqual(provenance["source_url"], server["repo"])
                self.assertEqual(provenance["commit"], server["commit"])
                self.assertTrue(re.fullmatch(r"[0-9a-f]{40}", provenance["commit"]))
                self.assertEqual(provenance["license"], server["license"])
                self.assertEqual(provenance["task"], server["task"])
                self.assertEqual(provenance["selected_tool"], server["tool"])

    def test_selected_tool_is_present_with_a_valid_input_schema(self):
        for server in capture.SERVERS:
            with self.subTest(server=server["key"]):
                tools = load_snapshot(server["key"])["native_tools_list"]["result"]["tools"]
                tool = next(tool for tool in tools if tool["name"] == server["tool"])
                self.assertEqual(tool["inputSchema"]["type"], "object")

    def test_captured_offline_with_placeholders_only(self):
        for server in capture.SERVERS:
            with self.subTest(server=server["key"]):
                capture_info = load_snapshot(server["key"])["provenance"]["capture"]
                if server.get("needs_caldav"):
                    self.assertIn("internal", capture_info["network"])
                else:
                    self.assertEqual(capture_info["network"], "none")
                self.assertEqual(capture_info["method"], "tools/list only; no tool called")
                for value in capture_info["placeholder_env"].values():
                    looks_placeholder = ("placeholder" in value or value.startswith("/secrets/")
                                         or value.startswith("http://sdg-capture") or value == "capture")
                    self.assertTrue(looks_placeholder, value)


class CaptureHelperTests(unittest.TestCase):
    def test_http_body_keeps_the_message_bytes_unchanged(self):
        message = '{"jsonrpc":"2.0","id":2,"result":{"tools":[]}}'
        self.assertEqual(capture._message_bytes_from_http_body(message), message.encode())
        event = f"event: message\ndata: {message}\n\n"
        self.assertEqual(capture._message_bytes_from_http_body(event), message.encode())
        with self.assertRaises(ValueError):
            capture._message_bytes_from_http_body("event: ping\n\n")

    def test_tools_from_pages_joins_pages_and_rejects_errors(self):
        pages = [b'{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"a"}],"nextCursor":"x"}}',
                 b'{"jsonrpc":"2.0","id":3,"result":{"tools":[{"name":"b"}]}}']
        self.assertEqual([tool["name"] for tool in capture.tools_from_pages(pages)], ["a", "b"])
        with self.assertRaises(RuntimeError):
            capture.tools_from_pages([b'{"jsonrpc":"2.0","id":2,"error":{"code":-1}}'])


if __name__ == "__main__":
    unittest.main()
