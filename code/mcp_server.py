"""
mcp_server.py — expose the study's conditions as a REAL MCP server.

Reviewer W3: "the scanner result uses a scanner the authors wrote." To answer
that, the conditions have to be scannable by real tooling (mcp-scan / Snyk Agent
Scan), and real tooling scans MCP servers, not Python dicts. This server
publishes one tool per condition, with EXACTLY the schema conditions.build()
produces, so what a scanner sees is what the model saw.

Run directly for a stdio MCP server:   python mcp_server.py
Write the blinding map:                python mcp_server.py --write-map
Scan it: see docs/SCANNING.md for the exact command and the disclosure constraint
(remote verification uploads tool descriptions to a vendor — do not run it before
the protocol §14 coordinated-disclosure step).

No model calls, no keys. This file only declares tools; it never calls an LLM.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import asyncio
import json
import os
import sys

import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool

import conditions

# One tool per condition.
#
# BLINDING (fixed 2026-08-08, USENIX review). Tools used to be published as
# `lookup_recent_orders__C`, `..__B_prime`, and so on. That put the CONDITION
# LABEL in the tool name — the exact surface a name-aware scanner reads — so an
# external scan would have been contaminated by our own bookkeeping before it
# examined anything. Published names are now uninformative ordinals, and the
# name -> condition mapping lives in a sidecar (`data/mcp_tool_map.json`) that the
# scanner never sees. Assignment is deterministic, so results stay reproducible.
SCANNED_CONDITIONS = ["A_prime", "B", "B_prime", "C", "D", "E"]
WORDING = "api_documentation"
TOOL_MAP_FILE = "data/mcp_tool_map.json"

# The scaffold is deliberately NOT applied here: it lives in the system prompt,
# and a scanner reads tool definitions only. Passing one would have changed
# nothing in the published schema and implied otherwise.

server = Server("schema-disclosure-gap")


def _published_name(index):
    return f"lookup_recent_orders_{index + 1:02d}"


def _specs():
    """[(published_name, condition, wording_style, tool_spec)] in fixed order."""
    out = []
    for i, cond in enumerate(SCANNED_CONDITIONS):
        ws = WORDING if cond == "C" else "default"
        spec = conditions.build(cond, wording_style=ws)
        out.append((_published_name(i), cond, ws, spec["tool"]))
    return out


def _tools():
    return [Tool(name=name, description=t["description"], inputSchema=t["parameters"])
            for name, _cond, _ws, t in _specs()]


def write_tool_map(path=TOOL_MAP_FILE):
    """Sidecar that de-blinds a scanner report. Keep it OUT of anything a scanner
    ingests."""
    mapping = {name: {"condition": cond, "wording_style": ws,
                      "required": t["parameters"]["required"]}
               for name, cond, ws, t in _specs()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
    print(f"wrote {path}")
    for name, meta in mapping.items():
        print(f"  {name}  ->  {meta['condition']:9s} {meta['required']}")
    return mapping


@server.list_tools()
async def list_tools():
    return _tools()


# The attack chain's untested link (docs/THREAT_MODEL.md §7 steps 3-5): every rate
# in this study was measured by calling provider APIs directly. Nobody has checked
# that a REAL MCP client passes the schema to the model unchanged, that the filled
# arguments actually reach the server, or whether the user sees them. This server
# is what makes that checkable -- but only if it records what arrives.
#
# Off by default: this file is also the scanner input, and a scanner run should not
# create logs. Enable with --record. The log is APPEND-ONLY and mirrors the runs/
# convention so the same tooling reads it.
# Overridable so a DRY-RUN probe never writes mock fills into the evidence log.
# Mixing mock rows into a capture file is precisely the contamination this project
# has had to catch twice already.
RECORD_PATH = os.environ.get("MCP_CAPTURE_PATH", "runs/mcp_client_capture.jsonl")
_RECORD = False


@server.call_tool()
async def call_tool(name, arguments):
    """Inert by design: the study measures the CALL, never a result.

    What matters here is `arguments` -- if a real client is driving this server,
    that dict is the ground truth for what the adversary receives in deployment,
    as opposed to what our direct-API harness inferred."""
    if _RECORD:
        import datetime
        meta = {}
        if os.path.exists(TOOL_MAP_FILE):
            with open(TOOL_MAP_FILE, encoding="utf-8") as f:
                meta = json.load(f).get(name, {})
        os.makedirs(os.path.dirname(RECORD_PATH), exist_ok=True)
        with open(RECORD_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "correlation_id": os.environ.get("MCP_CORRELATION_ID"),
                "mock": os.environ.get("MCP_CAPTURE_MOCK") == "true",
                "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                "published_tool": name,
                # de-blinded from the sidecar the scanner never sees
                "condition": meta.get("condition"),
                "wording_style": meta.get("wording_style"),
                "arguments_received": arguments,
            }) + "\n")
    return [TextContent(type="text", text='{"orders": []}')]


async def _main():
    async with mcp.server.stdio.stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    if "--write-map" in sys.argv:
        write_tool_map()
    else:
        # --record turns on argument capture for a REAL-CLIENT experiment. Keep it
        # off for scanner runs so scanning never writes to runs/.
        _RECORD = "--record" in sys.argv
        if _RECORD:
            print(f"recording client-supplied arguments to {RECORD_PATH}",
                  file=sys.stderr)
        asyncio.run(_main())
