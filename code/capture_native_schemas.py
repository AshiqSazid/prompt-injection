"""Capture the real tools/list of the 8 selected MCP servers and freeze them.

For each server in SERVERS (the selection in docs/NATIVE_SCHEMA_SHORTLIST.md):

  1. check out its source at the pinned commit      (.cache/native_src/, gitignored)
  2. build a Docker image                             (network allowed: downloads)
  3. start the server with NO network and placeholder settings
  4. send only `initialize` and `tools/list`         (no tool is ever called)
  5. save the exact response bytes                   (data/source_snapshots/native/raw/)
  6. freeze it with schema_snapshot.validate()       (data/source_snapshots/native/)

Safety: third-party code runs only inside a container with no network (CalDAV
gets an internal-only network to reach a throwaway local calendar server), all
Linux capabilities dropped, and only placeholder settings. Nothing from this
machine's environment (API keys, .env) is passed in.

A frozen snapshot is never overwritten. Delete it by hand if a capture must be
redone, and record why.

    python code/capture_native_schemas.py                 # all eight
    python code/capture_native_schemas.py --only files-go # one server
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
import argparse
import hashlib
import json
import queue
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

import schema_snapshot


SOURCE_DIR = Path(".cache/native_src")
CAPTURE_DIR = Path("data/source_snapshots/native/raw")   # exact response bytes, kept so hashes can be re-checked
SNAPSHOT_DIR = Path("data/source_snapshots/native")
DOCKER_DIR = Path("capture/docker")
SALEOR_HELPER = Path("capture/saleor_list_tools.py")

IMAGE_PREFIX = "sdg-capture"
CALDAV_NETWORK = "sdg-capture-net"
RADICALE_CONTAINER = "sdg-capture-radicale"

PROTOCOL_VERSION = "2025-06-18"
TIMEOUT_SECONDS = 120

# Hardening applied to every server container.
SAFE_RUN_FLAGS = [
    "--rm",
    "--cap-drop", "ALL",
    "--security-opt", "no-new-privileges",
    "--memory", "1g",
    "--pids-limit", "256",
]


# ---------------------------------------------------------------------------
# The selection. Commits, licenses and tools are copied from the shortlist.
#
#   dockerfile: path inside the repo if the author ships one, otherwise ours
#   network:    "none" for all but CalDAV
#   env:        placeholders only; none of these is a real credential
# ---------------------------------------------------------------------------

SERVERS = [
    {
        "key": "orders-shopify",
        "task": "orders",
        "repo": "https://github.com/GeLi2001/shopify-mcp",
        "commit": "c90faaf434023bd22c1beb6bd59ff735bca18fac",
        "license": "MIT",
        "tool": "get-customer-orders",
        "dockerfile": {"ours": "shopify.Dockerfile"},
        "env": {
            "SHOPIFY_ACCESS_TOKEN": "placeholder-not-a-real-token",
            "MYSHOPIFY_DOMAIN": "placeholder-store.myshopify.com",
        },
        "args": [],
        "mode": "stdio",
    },
    {
        "key": "orders-saleor",
        "task": "orders",
        "repo": "https://github.com/saleor/saleor-mcp",
        "commit": "09a084de0f22b8d3928a18b3904c356f2caeb284",
        "license": "AGPL-3.0",
        "license_note": "Only the captured tool schema is stored, not server code.",
        "tool": "orders",
        "dockerfile": {"repo": "Dockerfile"},
        "env": {},
        "args": [],
        "mode": "saleor_http",
    },
    {
        "key": "email-fastmail",
        "task": "email",
        "repo": "https://github.com/MadLlama25/fastmail-mcp",
        "commit": "aa183ce143f206bb46cf793aeeceef61e69543d6",
        "license": "MIT",
        "tool": "search_emails",
        "dockerfile": {"ours": "fastmail.Dockerfile"},
        "env": {},
        "args": [],
        "mode": "stdio",
    },
    {
        "key": "email-imap",
        "task": "email",
        "repo": "https://github.com/Wh1isper/mcp-email-server",
        "commit": "d364b64d2e89bd3686edb82624e1feb9a5562e1b",
        "license": "BSD-3-Clause",
        "tool": "list_emails_metadata",
        "dockerfile": {"repo": "Dockerfile"},
        "env": {},
        "args": [],
        "mode": "stdio",
    },
    {
        "key": "calendar-google",
        "task": "calendar",
        "repo": "https://github.com/nspady/google-calendar-mcp",
        "commit": "ac8bf687e7949824bbdd8a93986b1ba46ac6db37",
        "license": "MIT",
        "tool": "list-events",
        "dockerfile": {"repo": "Dockerfile"},
        "env": {"GOOGLE_OAUTH_CREDENTIALS": "/secrets/gcp-oauth.keys.json"},
        "dummy_google_keys": True,
        "args": [],
        "mode": "stdio",
    },
    {
        "key": "calendar-caldav",
        "task": "calendar",
        "repo": "https://github.com/dominik1001/caldav-mcp",
        "commit": "725de72d9dc26f3561a984387967273aa3cda0c9",
        "license": "MIT",
        "tool": "list-events",
        "dockerfile": {"ours": "caldav.Dockerfile"},
        "env": {
            "CALDAV_BASE_URL": f"http://{RADICALE_CONTAINER}:5232/",
            "CALDAV_USERNAME": "capture",
            "CALDAV_PASSWORD": "placeholder-not-a-real-password",
        },
        "needs_caldav": True,
        "args": [],
        "mode": "stdio",
    },
    {
        "key": "files-official",
        "task": "files",
        "repo": "https://github.com/modelcontextprotocol/servers",
        "commit": "f46d9578190b476b3501923ea8977d899e8db2cb",
        "license": "MIT / Apache-2.0 (transition)",
        "license_note": "GitHub reports NOASSERTION; LICENSE text is a mixed MIT to Apache-2.0 transition.",
        "tool": "read_text_file",
        "dockerfile": {"ours": "files-official.Dockerfile"},
        "build_note": ("The repo's src/filesystem/Dockerfile fails at this commit (npm "
                       "workspace error); built from the repo root with its own lockfile."),
        "env": {},
        "args": ["/tmp"],   # the one directory the server is allowed to serve
        "mode": "stdio",
    },
    {
        "key": "files-go",
        "task": "files",
        "repo": "https://github.com/mark3labs/mcp-filesystem-server",
        "commit": "ba3f07f22c309d932fa9b1cebe1eb7c55fcbb83b",
        "license": "MIT",
        "tool": "read_file",
        "dockerfile": {"repo": "Dockerfile"},
        "env": {},
        "args": ["/tmp"],
        "mode": "stdio",
    },
]


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------

def run(command, **kwargs):
    """Run a command, fail loudly, return stdout as text."""
    result = subprocess.run(command, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}\n{result.stderr[-3000:]}")
    return result.stdout.strip()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def image_name(server):
    return f"{IMAGE_PREFIX}/{server['key']}:{server['commit'][:12]}"


# ---------------------------------------------------------------------------
# Step 1: source at the pinned commit.
# ---------------------------------------------------------------------------

def ensure_source(server):
    folder = SOURCE_DIR / server["key"]
    if not folder.exists():
        SOURCE_DIR.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--quiet", "--filter=blob:none", server["repo"] + ".git", str(folder)])
    run(["git", "-C", str(folder), "-c", "advice.detachedHead=false", "checkout", "--quiet", server["commit"]])

    actual = run(["git", "-C", str(folder), "rev-parse", "HEAD"])
    if actual != server["commit"]:
        raise RuntimeError(f"{server['key']}: checked out {actual}, expected {server['commit']}")
    return folder


# ---------------------------------------------------------------------------
# Step 2: build the image.
# ---------------------------------------------------------------------------

def build_image(server, source_folder):
    if "repo" in server["dockerfile"]:
        dockerfile = source_folder / server["dockerfile"]["repo"]
        dockerfile_label = f"repo:{server['dockerfile']['repo']}"
    else:
        dockerfile = DOCKER_DIR / server["dockerfile"]["ours"]
        dockerfile_label = f"ours:{dockerfile.as_posix()}"

    print(f"  building {image_name(server)} ({dockerfile_label})")
    run(["docker", "build", "--quiet", "-t", image_name(server), "-f", str(dockerfile), str(source_folder)])
    image_id = run(["docker", "image", "inspect", "--format", "{{.Id}}", image_name(server)])
    return image_id, dockerfile_label, sha256_bytes(dockerfile.read_bytes())


# ---------------------------------------------------------------------------
# The CalDAV helper server.
# ---------------------------------------------------------------------------

def start_radicale():
    existing = run(["docker", "network", "ls", "--format", "{{.Name}}"]).splitlines()
    if CALDAV_NETWORK not in existing:
        # --internal: containers on this network can talk to each other but
        # cannot reach the internet.
        run(["docker", "network", "create", "--internal", CALDAV_NETWORK])

    run(["docker", "build", "--quiet", "-t", f"{IMAGE_PREFIX}/radicale:local",
         "-f", str(DOCKER_DIR / "radicale.Dockerfile"), str(DOCKER_DIR)])
    subprocess.run(["docker", "rm", "-f", RADICALE_CONTAINER], capture_output=True)
    run(["docker", "run", "-d", "--name", RADICALE_CONTAINER, "--network", CALDAV_NETWORK,
         f"{IMAGE_PREFIX}/radicale:local"])

    check = ["docker", "exec", RADICALE_CONTAINER, "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5232/.web/')"]
    for _ in range(60):
        if subprocess.run(check, capture_output=True).returncode == 0:
            version = run(["docker", "exec", RADICALE_CONTAINER, "python", "-c",
                           "import radicale; print(radicale.VERSION)"])
            return version
        threading.Event().wait(1)
    raise RuntimeError("local Radicale server did not start")


def stop_radicale():
    subprocess.run(["docker", "rm", "-f", RADICALE_CONTAINER], capture_output=True)
    subprocess.run(["docker", "network", "rm", CALDAV_NETWORK], capture_output=True)


# ---------------------------------------------------------------------------
# Step 3-5: talk to a stdio server with plain JSON-RPC.
#
# A hand-written client rather than the SDK, so we keep the EXACT bytes the
# server sent for tools/list: the protocol asks for an original-byte SHA-256.
# ---------------------------------------------------------------------------

class StdioSession:
    def __init__(self, command):
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.lines = queue.Queue()
        self.stderr_lines = []
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)   # end of stream

    def _read_stderr(self):
        for line in self.process.stderr:
            self.stderr_lines.append(line.decode("utf-8", errors="replace"))

    def send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def wait_for_response(self, request_id):
        """Return the raw bytes of the response to request_id."""
        while True:
            try:
                line = self.lines.get(timeout=TIMEOUT_SECONDS)
            except queue.Empty:
                raise RuntimeError(f"timed out waiting for response {request_id}\n{self.stderr_tail()}")
            if line is None:
                raise RuntimeError(f"server exited before responding\n{self.stderr_tail()}")

            raw = line.rstrip(b"\r\n")
            if not raw.strip():
                continue
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                continue   # a server printed a non-JSON log line to stdout; ignore it
            if message.get("id") == request_id and ("result" in message or "error" in message):
                return raw

    def stderr_tail(self):
        return "".join(self.stderr_lines[-30:])

    def close(self):
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


def capture_stdio(server, container_name):
    command = ["docker", "run", "-i", "--name", container_name] + SAFE_RUN_FLAGS
    command += ["--network", CALDAV_NETWORK if server.get("needs_caldav") else "none"]
    for key, value in server["env"].items():
        command += ["-e", f"{key}={value}"]
    if server.get("dummy_google_keys"):
        keys_file = write_dummy_google_keys()
        command += ["-v", f"{keys_file.resolve()}:/secrets/gcp-oauth.keys.json:ro"]
    command += [image_name(server)] + server["args"]

    session = StdioSession(command)
    try:
        session.send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                      "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                                 "clientInfo": {"name": "schema-disclosure-gap-capture", "version": "1"}}})
        initialize_raw = session.wait_for_response(1)
        session.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        pages = []
        cursor = None
        request_id = 2
        while True:
            params = {"cursor": cursor} if cursor else {}
            session.send({"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": params})
            raw = session.wait_for_response(request_id)
            pages.append(raw)
            cursor = json.loads(raw).get("result", {}).get("nextCursor")
            request_id += 1
            if not cursor:
                break
        return initialize_raw, pages
    finally:
        session.close()
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


def capture_saleor(server, container_name):
    helper = SALEOR_HELPER.resolve()
    command = ["docker", "run", "--name", container_name] + SAFE_RUN_FLAGS + [
        "--network", "none",
        "-v", f"{helper}:/capture/saleor_list_tools.py:ro",
        "--entrypoint", "python",
        image_name(server), "/capture/saleor_list_tools.py",
    ]
    try:
        output = run(command, timeout=TIMEOUT_SECONDS)
    finally:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
    result = json.loads(output.splitlines()[-1])
    initialize_raw = _message_bytes_from_http_body(result["initialize_raw"])
    pages = []
    for body in result["tools_list_raw"]:
        pages.append(_message_bytes_from_http_body(body))
    return initialize_raw, pages


def _message_bytes_from_http_body(body):
    """The JSON-RPC message exactly as sent, from a plain or server-sent-event body.

    A server-sent event wraps the JSON on a `data:` line. We keep that line's
    text unchanged (no re-serialising), so its hash is of the server's bytes.
    """
    body = body.strip()
    if body.startswith("{"):
        return body.encode("utf-8")
    for line in body.splitlines():
        if line.startswith("data:"):
            return line[len("data:"):].strip().encode("utf-8")
    raise ValueError("no JSON-RPC message in response body")


def write_dummy_google_keys():
    """The example file the repo itself ships, with placeholder values only."""
    path = Path(".cache/native_capture_tmp/gcp-oauth.keys.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"installed": {
        "client_id": "placeholder-client-id.apps.googleusercontent.com",
        "client_secret": "placeholder-not-a-real-secret",
        "redirect_uris": ["http://localhost:3000/oauth2callback"],
    }}, indent=2))
    return path


# ---------------------------------------------------------------------------
# Step 6: save and freeze.
# ---------------------------------------------------------------------------

def tools_from_pages(pages):
    tools = []
    for raw in pages:
        message = json.loads(raw)
        if "error" in message:
            raise RuntimeError(f"tools/list returned an error: {message['error']}")
        tools.extend(message["result"]["tools"])
    return tools


def save_and_freeze(server, initialize_raw, pages, build_info, extra):
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    tools = tools_from_pages(pages)
    tool_names = [tool["name"] for tool in tools]
    if server["tool"] not in tool_names:
        raise RuntimeError(f"{server['key']}: selected tool {server['tool']!r} not in tools/list: {tool_names}")

    # The raw file IS the exact response bytes when there is one page (the
    # usual case). Multiple pages are joined, and each page's hash is kept.
    if len(pages) == 1:
        raw_bytes = pages[0]
    else:
        raw_bytes = json.dumps({"result": {"tools": tools}}).encode("utf-8")
    raw_path = CAPTURE_DIR / f"{server['key']}.tools_list.json"
    raw_path.write_bytes(raw_bytes)

    image_id, dockerfile_label, dockerfile_sha = build_info
    provenance = {
        "source_url": server["repo"],
        "commit": server["commit"],
        "license": server["license"],
        "task": server["task"],
        "selected_tool": server["tool"],
        "capture": {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "method": "tools/list only; no tool called",
            "transport": "streamable-http inside container" if server["mode"] == "saleor_http" else "stdio",
            "network": CALDAV_NETWORK + " (internal, no internet)" if server.get("needs_caldav") else "none",
            "protocol_version_requested": PROTOCOL_VERSION,
            "docker_image_id": image_id,
            "dockerfile": dockerfile_label,
            "dockerfile_sha256": dockerfile_sha,
            "docker_server_version": run(["docker", "version", "--format", "{{.Server.Version}}"]),
            "placeholder_env": server["env"],
            "server_args": server["args"],
            "initialize_response_sha256": sha256_bytes(initialize_raw),
            "tools_list_page_sha256": [sha256_bytes(raw) for raw in pages],
            "tool_count": len(tools),
        },
    }
    if "license_note" in server:
        provenance["license_note"] = server["license_note"]
    if "build_note" in server:
        provenance["capture"]["build_note"] = server["build_note"]
    provenance["capture"].update(extra)

    result = schema_snapshot.validate(json.loads(raw_bytes), provenance)
    result["source_sha256"] = sha256_bytes(raw_bytes)
    result["initialize_response"] = json.loads(initialize_raw)

    snapshot_path = SNAPSHOT_DIR / f"{server['key']}.json"
    # "x" mode: refuse to overwrite a snapshot that already exists.
    with open(snapshot_path, "x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
    return snapshot_path, len(tools)


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

def capture_one(server):
    snapshot_path = SNAPSHOT_DIR / f"{server['key']}.json"
    if snapshot_path.exists():
        print(f"- {server['key']}: already frozen at {snapshot_path}, skipped")
        return "skipped"

    print(f"- {server['key']}")
    source = ensure_source(server)
    build_info = build_image(server, source)
    container_name = f"sdg-capture-{server['key']}"

    extra = {}
    if server.get("needs_caldav"):
        extra["radicale_version"] = start_radicale()
    try:
        if server["mode"] == "saleor_http":
            initialize_raw, pages = capture_saleor(server, container_name)
        else:
            initialize_raw, pages = capture_stdio(server, container_name)
    finally:
        if server.get("needs_caldav"):
            stop_radicale()

    path, count = save_and_freeze(server, initialize_raw, pages, build_info, extra)
    print(f"  frozen: {path} ({count} tools, selected {server['tool']!r} present)")
    return "captured"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="capture one server by key, e.g. files-go")
    args = parser.parse_args()

    servers = SERVERS
    if args.only:
        servers = [server for server in SERVERS if server["key"] == args.only]
        if not servers:
            raise SystemExit(f"unknown key {args.only!r}; known: {[s['key'] for s in SERVERS]}")

    outcomes = {}
    for server in servers:
        try:
            outcomes[server["key"]] = capture_one(server)
        except Exception as error:  # noqa: BLE001 -- report every server, keep going
            outcomes[server["key"]] = f"FAILED: {error}"
            print(f"  FAILED: {error}")

    print("\nsummary:")
    for key, outcome in outcomes.items():
        print(f"  {key:18s} {outcome.splitlines()[0]}")


if __name__ == "__main__":
    main()
