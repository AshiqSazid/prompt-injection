"""
harvest_real_tools.py — build a corpus of REAL MCP tool schemas for condition C.

Fixes the "n = 1 synthetic tool" objection, which is the most-repeated external
validity criticism of this study. Every rate in the paper so far comes from one
hand-written `lookup_recent_orders`. This harvests the authentic tools from the 45
live MCP servers in MCPTox (arXiv 2508.14925) so condition C can be appended to
schemas the authors did not write.

PARSING NOTE, because it changes what is trustworthy here: each server's
`clean_system_promot` lists every tool with its description and arguments, and
`clean_querys` holds realistic user requests for that server. The two lists CANNOT
be paired by index -- `tool_names` is alphabetised and `clean_querys` is not, so
position i in one does not correspond to position i in the other (verified: for
FileSystem, index 0 is `create_directory` against a query asking to READ a file).

So each tool is matched to the query with the highest token overlap against its
name and description, greedily, one query per tool. The match score is recorded in
the output so a reviewer can audit or discard weak pairings, and `--min-score`
drops the ones that are too weak to be plausible.

Usage:
    python harvest_real_tools.py                 # -> data/real_tools.json
    python harvest_real_tools.py --n 25          # cap the corpus size
    python harvest_real_tools.py --show          # print what was selected
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import json
import os
import re
import sys

CACHE = ".cache/mcptox_response_all.json"
OUT = "data/real_tools.json"
_STOP = {"the", "a", "an", "to", "of", "for", "in", "on", "and", "or", "with", "my",
         "me", "i", "please", "want", "need", "it", "this", "that", "from", "is",
         "are", "be", "can", "you", "your", "all", "get", "use", "using", "at", "by"}


def _toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if len(w) > 2 and w not in _STOP}


def parse_tools(servers):
    rx_tool = re.compile(r"^Tool:\s*(.+)$")
    rx_arg = re.compile(r"^-\s*([A-Za-z_][A-Za-z0-9_.\-]*)\s*:\s*(.*)$")
    out = []
    for sname, s in servers.items():
        lines = (s.get("clean_system_promot") or "").splitlines()
        queries = [q for q in (s.get("clean_querys") or [])
                   if isinstance(q, str) and q.strip()]
        cur = desc = None
        params = []

        def flush():
            if cur and desc and params:
                out.append({"server": sname, "name": cur, "description": desc,
                            "params": list(params), "_queries": queries})
        for i, raw in enumerate(lines):
            l = raw.strip()
            m = rx_tool.match(l)
            if m:
                flush()
                cur, desc, params = m.group(1).strip(), None, []
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
                if nxt.startswith("Description:"):
                    desc = nxt[len("Description:"):].strip()
                continue
            m = rx_arg.match(l)
            if m and cur:
                name = m.group(1)
                d = re.sub(r"\s*\(required\)$", "", m.group(2).strip())
                if d.lower().startswith("no description"):
                    d = ""
                params.append({"name": name, "description": d,
                               "required": "(required)" in raw})
        flush()
    return out


def match_queries(tools):
    """Greedy best-overlap assignment of one server query per tool."""
    by_server = {}
    for t in tools:
        by_server.setdefault(t["server"], []).append(t)
    for server, group in by_server.items():
        queries = group[0]["_queries"]
        scored = []
        for t in group:
            tt = _toks(t["name"].replace("_", " ")) | _toks(t["description"])
            for qi, q in enumerate(queries):
                scored.append((len(tt & _toks(q)), t["name"], qi))
        scored.sort(reverse=True)
        used_q, used_t = set(), set()
        for score, tname, qi in scored:
            if tname in used_t or qi in used_q or score == 0:
                continue
            used_t.add(tname)
            used_q.add(qi)
            for t in group:
                if t["name"] == tname:
                    t["query"] = queries[qi]
                    t["match_score"] = score
    return tools


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25, help="max tools to keep")
    ap.add_argument("--min-score", type=int, default=2)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(CACHE):
        raise SystemExit(f"{CACHE} missing — run: python harvest_benign_fields.py")
    with open(CACHE, encoding="utf-8") as f:
        servers = json.load(f)["servers"]

    tools = match_queries(parse_tools(servers))
    usable = [t for t in tools
              if t.get("query") and t.get("match_score", 0) >= a.min_score
              and t["description"] and any(p["required"] for p in t["params"])]
    # one tool per server first, for maximum schema diversity, then fill up
    seen, picked = set(), []
    for t in sorted(usable, key=lambda x: -x["match_score"]):
        if t["server"] not in seen:
            seen.add(t["server"])
            picked.append(t)
    for t in sorted(usable, key=lambda x: -x["match_score"]):
        if len(picked) >= a.n:
            break
        if t not in picked:
            picked.append(t)
    picked = picked[:a.n]

    for t in picked:
        t.pop("_queries", None)
    payload = {
        "_provenance": {
            "source": "MCPTox (arXiv 2508.14925) clean_system_promot / clean_querys",
            "cache": CACHE,
            "n_tools_parsed": len(tools),
            "n_usable": len(usable),
            "n_selected": len(picked),
            "servers": sorted({t["server"] for t in picked}),
            "query_matching": "greedy best token-overlap; tool_names is alphabetised "
                              "while clean_querys is not, so index pairing is INVALID",
            "min_match_score": a.min_score,
        },
        "tools": picked,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"parsed {len(tools)} tools, {len(usable)} usable, selected {len(picked)} "
          f"across {len(seen)} servers -> {OUT}")
    if a.show:
        for t in picked:
            req = [p["name"] for p in t["params"] if p["required"]]
            print(f"\n  {t['server']}/{t['name']}  (match={t['match_score']})")
            print(f"    required: {req}")
            print(f"    query:    {t['query'][:90]}")
    if len(picked) < 20:
        print(f"WARNING: only {len(picked)} tools; the objection is 'n=1 tool', so "
              "aim for >= 20", file=sys.stderr)


if __name__ == "__main__":
    main()
