"""Ask the Saleor MCP server for tools/list, from INSIDE its own container.

Saleor serves MCP over HTTP rather than stdio. Running this helper inside the
same container lets the capture use `--network none`: the request only ever
travels over the container's loopback interface.

Prints one JSON object to stdout:
    {"initialize_raw": "<response body>", "tools_list_raw": ["<page 1 body>", ...]}
Bodies are kept exactly as received, so the capture can hash the original bytes.
Only initialize and tools/list are sent. No tool is ever called.
"""
import json
import subprocess
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:8000"
MCP_URL = BASE + "/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def start_server():
    return subprocess.Popen(
        ["uvicorn", "saleor_mcp.main:app", "--host=127.0.0.1", "--port=8000"],
        stdout=subprocess.DEVNULL,
        stderr=sys.stderr,
    )


def wait_until_healthy(seconds=60):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("Saleor MCP server did not become healthy")


def post(message):
    request = urllib.request.Request(MCP_URL, data=json.dumps(message).encode(),
                                     headers=HEADERS, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def json_from_body(body):
    """A streamable-HTTP reply is either plain JSON or a server-sent event."""
    body = body.strip()
    if body.startswith("{"):
        return json.loads(body)
    for line in body.splitlines():
        if line.startswith("data:"):
            return json.loads(line[len("data:"):].strip())
    raise ValueError("no JSON-RPC message in response body")


def main():
    server = start_server()
    try:
        wait_until_healthy()
        initialize_raw = post({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "schema-disclosure-gap-capture", "version": "1"}},
        })

        pages = []
        cursor = None
        request_id = 2
        while True:
            params = {"cursor": cursor} if cursor else {}
            body = post({"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": params})
            pages.append(body)
            cursor = json_from_body(body).get("result", {}).get("nextCursor")
            request_id += 1
            if not cursor:
                break

        print(json.dumps({"initialize_raw": initialize_raw, "tools_list_raw": pages}))
    finally:
        server.terminate()


if __name__ == "__main__":
    main()
