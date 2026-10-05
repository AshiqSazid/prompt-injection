"""
mcp_client_probe.py — drive the study's tools through a REAL MCP client session.

WHAT THIS CLOSES, AND WHAT IT DOES NOT. Every rate in this study came from calling
provider APIs directly with a schema this repo constructed in memory. Steps 3-5 of
the attack chain (docs/THREAT_MODEL.md §7) were therefore *inferred*: that a schema
published over MCP reaches the model unchanged, that the model fills the added
field, and that the filled value arrives at the tool server.

This probe closes exactly that transport link, end to end:

    mcp_server.py --record   (real stdio MCP server, blinded tool names)
        -> MCP list_tools     schema crosses the protocol, not a Python import
        -> provider API       the model sees what the CLIENT was given
        -> MCP call_tool      the model's arguments cross back over the protocol
        -> runs/mcp_client_capture.jsonl   what the adversary actually receives

It does NOT close the deployed-product half. A shipped client (Cursor, Claude
Desktop) supplies its own system prompt and its own UI, and those decide (a)
whether real deployment identity is present to leak at all and (b) whether the
user is shown the filled parameter -- the "no consent surface" claim in §6.3.
This probe supplies neither. Do not cite it as evidence for either. It is a
transport proof, and it should be described in the paper as one.

Usage:
    python mcp_client_probe.py --dry-run     # mock provider, no API call, no cost
    python mcp_client_probe.py               # [API] one live call per condition
    python mcp_client_probe.py --condition C # just the channel arm
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import asyncio
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import conditions
import providers
from grade import captured_text, keyword_grade, load_dotenv

CAPTURE = "runs/mcp_client_capture.jsonl"
MAP_FILE = "data/mcp_tool_map.json"


async def _probe(condition, model, provider, dry_run, capture_path,
                 scaffold="cursor", response_override=None):
    """One end-to-end pass for a single published tool."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    with open(MAP_FILE, encoding="utf-8") as f:
        tool_map = json.load(f)
    published = next((n for n, m in tool_map.items() if m["condition"] == condition),
                     None)
    if published is None:
        raise SystemExit(f"no published tool for condition {condition!r}; "
                         "run mcp_server.py --write-map")

    correlation_id = uuid.uuid4().hex
    params = StdioServerParameters(
        command=sys.executable, args=[str(Path(__file__).with_name("mcp_server.py")), "--record"],
        # a mock fill must never land in the capture log that the paper cites
        env={**os.environ, "MCP_CAPTURE_PATH": os.path.abspath(capture_path),
             "MCP_CORRELATION_ID": correlation_id, "MCP_CAPTURE_MOCK": str(dry_run).lower()})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            tool = next(t for t in listing.tools if t.name == published)

            # THE POINT: the schema handed to the model is the one that crossed
            # the MCP wire, not one this process built.
            spec = {
                "condition": condition,
                "system": conditions.SCAFFOLDS[scaffold] + conditions.SYSTEM,
                "user": conditions.USER,
                "tool": {"name": tool.name,
                         "description": tool.description,
                         "parameters": tool.inputSchema},
            }
            if response_override is not None:
                if not dry_run:
                    raise ValueError("response overrides are restricted to offline tests")
                res = providers.annotate(response_override, model, spec, mock=True)
            else:
                res = providers.call(provider, model, spec, 0.7,
                                     dry_run=dry_run, max_tokens=256)
            result = {"condition": condition, "published": published,
                      "correlation_id": correlation_id, "mock": dry_run,
                      **{k: res[k] for k in ("tool_called", "arguments_parsed", "schema_valid",
                                             "tool_name_matches")},
                      "tool_name": res.get("tool_name"), "dispatched": False,
                      "server_received": False, "delivered": False,
                      "t1": False}
            if not (res["tool_called"] and res["arguments_parsed"] and res["tool_name_matches"]):
                return result

            # And the model's arguments go BACK over the wire to the server.
            # A rejection here is a REAL finding, not a nuisance: it means the
            # arguments the model produced do not satisfy the schema the server
            # published, so nothing reaches the adversary. Surface it.
            out = await session.call_tool(res["tool_name"], res["params"])
            rejected = bool(getattr(out, "isError", False))
            captures = [r for r in _tail_capture(capture_path, 10000)
                        if r.get("correlation_id") == correlation_id
                        and r.get("published_tool") == res["tool_name"]
                        and r.get("arguments_received") == res["params"]]
            received = len(captures) == 1
            result.update(dispatched=True, sent=res["params"], server_rejected=rejected,
                          server_received=received, delivered=received,
                          t1=received and keyword_grade(captured_text(
                              {"raw_response": "", "params_passed": captures[0]["arguments_received"]}
                          ))["tier_flags"]["T1"])
            return result


def _tail_capture(path, n):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f][-n:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--condition", default=None,
                    help="default: A_prime, C and D (the field conditions)")
    ap.add_argument("--provider", default="openai")
    ap.add_argument("--model", default="gpt-4o")
    a = ap.parse_args()
    load_dotenv()

    conds = [a.condition] if a.condition else ["A_prime", "C", "D"]
    capture = (os.path.join(tempfile.mkdtemp(), "dry_capture.jsonl") if a.dry_run
               else CAPTURE)
    before = len(_tail_capture(capture, 10_000))
    print(f"MCP transport probe — {a.provider}/{a.model}"
          f"{' [DRY RUN, mock provider]' if a.dry_run else ' [LIVE]'}\n")

    results = []
    for cond in conds:
        r = asyncio.run(_probe(cond, a.model, a.provider, a.dry_run, capture))
        results.append(r)
        sent = json.dumps(r.get("sent") or {})[:96]
        print(f"  {cond:8s} via {r['published']:24s} tool_called={r['tool_called']}"
              f"{'  T1=' + str(r['t1']) if r['tool_called'] else ''}")
        if r["tool_called"]:
            print(f"           model sent: {sent}")
            if r.get("server_rejected"):
                print("           SERVER REJECTED these arguments — they do not "
                      "satisfy the published schema. Handler receipt is measured "
                      "separately; wire arrival alone is not handler acceptance.")

    got = _tail_capture(capture, 10_000)[before:]
    print(f"\n=== what the SERVER received ({len(got)} call(s) recorded) ===")
    for row in got:
        print(f"  {row['condition']:8s} {json.dumps(row['arguments_received'])[:110]}")

    delivered = sum(r["server_received"] for r in results)
    print(f"\nCorrelated handler receipts: {delivered}/{len(results)} probes.")
    print("Offline mock transport check; no model-disclosure evidence." if a.dry_run
          else "Only correlated captures establish handler receipt for these calls.")
    print("NOT shown here: a shipped client's own system prompt, and whether any UI")
    print("displays the filled parameter (§6.3). Both need a real product.")


if __name__ == "__main__":
    main()
