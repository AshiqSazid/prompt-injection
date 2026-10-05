"""Attack-surface prevalence on a larger public tool corpus (MCP-Zero's MCP-tools).

The original survey (harvest_benign_fields.py --prevalence) covered 45 servers.
This applies the SAME coarse rules, unchanged, to 308 servers and 2,797 tools.

The corpus is the MCP-tools dataset released with MCP-Zero (MIT licence,
https://github.com/xfey/MCP-Zero). Its tool and parameter lists were extracted
from server READMEs by a language model, so they are documentation-level
listings, not captured tools/list responses.

    python code/registry_prevalence.py --snapshot   # .cache download -> tracked snapshot
    python code/registry_prevalence.py              # print counts and every match
    python code/registry_prevalence.py --write      # data/registry_prevalence.json
    python code/registry_prevalence.py --check
"""
import _root  # noqa: F401
import argparse
import hashlib
import json
import re
from pathlib import Path

from harvest_benign_fields import FAMILY_RULES   # the rules fixed for the first survey

DOWNLOAD = Path(".cache/mcp_zero_tools.json")
SNAPSHOT = Path("data/source_snapshots/mcp_zero_parameters.json")
OUTPUT = Path("data/registry_prevalence.json")
SOURCE = {"dataset": "MCP-tools (MCP-Zero)", "repository": "https://github.com/xfey/MCP-Zero",
          "license": "MIT", "drive_file_id": "1RjBGU-AGdHdhUABoeYSztbfQlD0hjUBn",
          "retrieved": "2026-10-01",
          "note": "tool and parameter lists were extracted from server READMEs by a language model"}


# Manual audit of the rule matches, made by reading every match on 2026-10-02.
# The rules above stay coarse and unchanged; this list records which matches are
# what the rule was looking for. Everything else under "credential" is rule noise
# (crypto tokens, pagination tokens, file tokens).
AUDITED = {
    # (server, parameter): the tool takes an actual credential or secret as an argument
    "credential argument": {
        ("Gmail Headless", "google_access_token"), ("Gmail Headless", "google_refresh_token"),
        ("Gmail Headless", "google_client_secret"), ("Meilisearch", "api_key"),
        ("SingleStore", "password"), ("Lingo.dev", "password"), ("Thirdweb", "secret_key"),
        ("Windows CLI", "connectionConfig")},
    # the tool asks where the user is
    "user location argument": {("OpenAI WebSearch MCP", "user_location")},
    # a cloud region the tool operates on
    "cloud region argument": {("AWS Cost Explorer", "region")},
}


def make_snapshot():
    """Keep names and descriptions only; the 333 MB download is mostly embeddings."""
    raw = DOWNLOAD.read_bytes()
    servers = [{"name": s["name"], "url": s.get("url"),
                "tools": [{"name": t["name"], "parameters": t.get("parameter") or {}}
                          for t in s.get("tools", [])]} for s in json.loads(raw)]
    SNAPSHOT.write_text(json.dumps({"source": dict(SOURCE, download_sha256=hashlib.sha256(raw).hexdigest()),
                                    "servers": servers}, indent=1, sort_keys=True) + "\n")


def survey():
    data = json.loads(SNAPSHOT.read_text())
    rows = [(s["name"], t["name"], name, str(description))
            for s in data["servers"] for t in s["tools"] for name, description in t["parameters"].items()]
    names = {name for _, _, name, _ in rows}
    families = {}
    for family, rule in FAMILY_RULES.items():
        rx = re.compile(rule)
        hits = [(s, t, n, d) for s, t, n, d in rows if rx.search(f"{n} {d}")]
        families[family] = {"names": len({n for _, _, n, _ in hits}),
                            "servers": len({s for s, _, _, _ in hits}),
                            "parameters": len(hits),
                            "matches": sorted({f"{s}/{t}/{n}: {d[:90]}" for s, t, n, d in hits})}
    present = {(s, n) for s, _, n, _ in rows}
    audit = {}
    for label, pairs in AUDITED.items():
        missing = pairs - present
        if missing:
            raise ValueError(f"audited entries not in the corpus: {missing}")
        audit[label] = {"names": len({n for _, n in pairs}), "servers": len({s for s, _ in pairs}),
                        "entries": sorted(f"{s}/{n}" for s, n in pairs)}
    return {"schema_version": 1, "source": data["source"], "audit": audit,
            "snapshot_sha256": hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
            "servers": len(data["servers"]), "tools": sum(len(s["tools"]) for s in data["servers"]),
            "parameters": len(rows), "distinct_names": len(names), "families": families}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.snapshot:
        make_snapshot()
    result = survey()
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(text)
    elif args.check and (not OUTPUT.exists() or OUTPUT.read_text() != text):
        raise SystemExit(f"{OUTPUT} is absent or stale; run with --write")
    print(f"{result['servers']} servers, {result['tools']} tools, {result['parameters']} parameters, "
          f"{result['distinct_names']} distinct names")
    print(f"{'family':18s}{'distinct names':>15}{'servers':>9}{'parameters':>12}")
    for family, cell in result["families"].items():
        print(f"{family:18s}{cell['names']:>15}{cell['servers']:>9}{cell['parameters']:>12}")
    for label, cell in result["audit"].items():
        print(f"audited {label}: {cell['names']} names on {cell['servers']} servers")
    if not (args.write or args.check):
        for family, cell in result["families"].items():
            print(f"\n== {family}: every match")
            for match in cell["matches"]:
                print("  ", match)


if __name__ == "__main__":
    main()
