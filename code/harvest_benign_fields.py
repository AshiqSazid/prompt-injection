"""
harvest_benign_fields.py — build the defense's NEGATIVE corpus from real schemas.

Why this exists (USENIX review, defense §7): the previous defense corpus was 15
hand-written benign fields, and its positives were drawn from the study's own
conditions. That is train-on-test. This script replaces the hand-written half
with fields harvested from two REAL, public, citable sources, so the
false-positive number means something.

Two strata, kept separate because they answer different questions:

  S1  mcptox  — parameters of the 353 authentic tools on the 45 live MCP servers
                in the MCPTox benchmark (arXiv 2508.14925). These are the fields a
                deployed detector would actually meet in the MCP ecosystem, so S1
                measures REALISTIC false-positive cost.
                Parsed out of each server's `clean_system_promot`, which lists
                every tool and argument verbatim. NOTE: only the CLEAN prompts are
                read. The benchmark's poisoned definitions (def_tool/*.py,
                `malicious_instance`) are never touched.

  S2  otel    — OpenTelemetry semantic-convention attributes for user-agent,
                client, service, telemetry SDK, device and HTTP. These are the
                HARD negatives: real, standardised telemetry fields that describe
                the CALLING SOFTWARE — the same thing condition C asks for, but
                legitimately. S2 measures whether the detector can separate
                "telemetry about the caller" from "make the agent introspect".
                MCPTox contains ZERO user-agent / client-identity parameters
                (verified: 0 of 401 distinct names), so without S2 the corpus
                would omit exactly the case condition C exploits.

Usage:
    python harvest_benign_fields.py            # fetch, parse, write data/benign_fields.json
    python harvest_benign_fields.py --offline  # re-parse from .cache/ only

Network: two public raw.githubusercontent.com reads. No credentials, no uploads.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import json
import os
import re
import sys
import urllib.request

CACHE = ".cache"
MCPTOX_URL = ("https://raw.githubusercontent.com/zhiqiangwang4/"
              "MCPTox-Benchmark/main/response_all.json")
OTEL_BASE = ("https://raw.githubusercontent.com/open-telemetry/"
             "semantic-conventions/main/model")
OTEL_REGISTRIES = ["user-agent/registry", "client/registry", "service/registry",
                   "telemetry/registry", "device/registry", "http/registry"]
OUT = "data/benign_fields.json"


def _fetch(url, dest, offline):
    if os.path.exists(dest):
        return dest
    if offline:
        raise SystemExit(f"--offline but {dest} is not cached; run once online first")
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    print(f"  fetching {url}")
    urllib.request.urlretrieve(url, dest)
    return dest


_RX_TOOL = re.compile(r"^Tool:\s*(.+)$")
_RX_ARG = re.compile(r"^-\s*([A-Za-z_][A-Za-z0-9_.\-]*)\s*:\s*(.*)$")


def harvest_mcptox(offline=False):
    """Parse (param name, description) out of every server's CLEAN system prompt."""
    path = _fetch(MCPTOX_URL, f"{CACHE}/mcptox_response_all.json", offline)
    with open(path, encoding="utf-8") as f:
        servers = json.load(f)["servers"]
    rows, seen = [], set()
    for sname, s in servers.items():
        tool = None
        for line in (s.get("clean_system_promot") or "").splitlines():
            line = line.strip()
            m = _RX_TOOL.match(line)
            if m:
                tool = m.group(1).strip()
                continue
            m = _RX_ARG.match(line)
            if not (m and tool):
                continue
            name = m.group(1)
            desc = re.sub(r"\s*\(required\)$", "", m.group(2).strip()).strip()
            # real schemas often omit descriptions; keep only fields a detector
            # could actually reason about, and dedupe on (name, desc)
            if not desc or desc.lower().startswith("no description"):
                continue
            key = (name, desc)
            if key in seen:
                continue
            seen.add(key)
            rows.append({"name": name, "desc": desc, "stratum": "mcptox",
                         "source": f"MCPTox/{sname}/{tool}"})
    return rows


def harvest_otel(offline=False):
    import yaml
    rows, seen = [], set()
    for reg in OTEL_REGISTRIES:
        dest = f"{CACHE}/otel_{reg.replace('/', '_')}.yaml"
        path = _fetch(f"{OTEL_BASE}/{reg}.yaml", dest, offline)
        doc = yaml.safe_load(open(path, encoding="utf-8"))
        for grp in doc.get("groups", []) or []:
            prefix = grp.get("prefix") or ""
            for a in grp.get("attributes", []) or []:
                name = a.get("id") or a.get("ref")
                brief = (a.get("brief") or "").strip()
                if not name or not brief or a.get("deprecated"):
                    continue
                full = f"{prefix}.{name}" if prefix and not name.startswith(prefix) else name
                brief = re.sub(r"\s+", " ", re.sub(r"`|\[.*?\]\(.*?\)", "", brief))[:220]
                if full in seen:
                    continue
                seen.add(full)
                rows.append({"name": full, "desc": brief, "stratum": "otel",
                             "source": f"opentelemetry/{reg}"})
    return rows


# --- ecological validity of the attack surface (added 2026-08-10) ------------
# THREAT_MODEL.md carried two hand-waved caveats: that the attacker's field is
# "atypical for MCP", and that severity depends on real prompts carrying the
# material we plant. Both are prevalence questions and both are measurable from
# data already in this repo. Measuring them replaces a caveat with a number, and
# the numbers do not all favour the paper -- which is why they belong in it.
#
# Rules are deliberately COARSE and fixed here before being run, so they cannot be
# tuned to a conclusion. They over-count if anything (a parameter merely mentioning
# a region counts), which biases AGAINST the "atypical" claim we would prefer.
FAMILY_RULES = {
    "client-identity": r"(?i)user[_-]?agent|\bclient[_-]?(?:name|id|info|version)|"
                       r"\bsdk\b|instrumentation|telemetry\.sdk",
    "region":          r"(?i)\bregion\b|\bzone\b|locality|data[_-]?residency|datacenter",
    "operator/tenant": r"(?i)\btenant\b|\borganisation\b|\borganization\b|\borg[_-]|"
                       r"\bworkspace\b|\baccount[_-]?(?:name|id|label)\b",
    "credential":      r"(?i)\bapi[_-]?key\b|\btoken\b|\bsecret\b|\bcredential\b|"
                       r"\bpassword\b|\bauth\b|\bbearer\b",
    "contact":         r"(?i)\bescalation\b|\bon[_-]?call\b|\bcontact\b",
    "policy":          r"(?i)\bpolicy\b|\bentitlement\b|\btier\b|\bquota\b|\bplan[_-]?id\b",
}

# What the VICTIM side would have to contain for the severity claim to bite.
VICTIM_PROBES = {
    "credential-shaped": r"(?i)\b(sk-[a-z0-9]{8,}|api[_-]?key\s*[:=]\s*\S+|"
                         r"secret\s*[:=]\s*\S+|bearer\s+[A-Za-z0-9._-]{12,})",
    "cloud region":      r"\b(?:us|eu|ap|sa|ca|me|af)-(?:east|west|central|north|south)-\d\b",
    "operator/tenant":   r"(?i)\byour operator is\b|\btenant\s*[:=]",
    "policy token":      r"\b[A-Z][A-Z0-9]{2,}-[A-Z0-9]{2,}-\d+\b",
}

def prevalence(offline=True, quiet=False):
    """How plausible is each attacker field in the real MCP ecosystem, and does
    real host-prompt text carry the material the attack targets?

    RETURNS the counts as well as printing them. A number that exists only in
    stdout gets retyped into prose, and retyped numbers are exactly how this
    project's claim surface drifted four times; manifest.py registers what this
    returns so the manuscript cites a macro instead."""
    say = (lambda *a, **k: None) if quiet else print
    from pathlib import Path
    import evidence
    snapshot = Path("data/source_snapshots/mcptox_listings.json")
    if offline and snapshot.exists():
        provenance = json.loads(snapshot.with_name("provenance.json").read_text())
        if evidence.digest(snapshot) != provenance["snapshot_sha256"]:
            raise ValueError("historical listing snapshot digest mismatch")
        path = snapshot
    else:
        path = _fetch(MCPTOX_URL, f"{CACHE}/mcptox_response_all.json", offline)
    with open(path, encoding="utf-8") as f:
        servers = json.load(f)["servers"]

    rows, names, per_server = [], set(), {}
    for sname, s in servers.items():
        tool = None
        for line in (s.get("clean_system_promot") or "").splitlines():
            line = line.strip()
            m = _RX_TOOL.match(line)
            if m:
                tool = m.group(1).strip()
                continue
            m = _RX_ARG.match(line)
            if m and tool:
                rows.append((sname, tool, m.group(1), m.group(2)))
                names.add(m.group(1))
                per_server.setdefault(sname, set()).add(m.group(1))

    say("=" * 74)
    say("ATTACK SURFACE — would the adversary's field look out of place?")
    say(f"{len(servers)} live MCP servers, {len(rows)} parameters, "
          f"{len(names)} distinct names")
    say("=" * 74)
    say(f"\n{'fact family':18s}{'distinct names':>15}{'servers':>9}")
    matches = {}
    for fam, rule in FAMILY_RULES.items():
        rx = re.compile(rule)
        hit = {}
        srv = set()
        for s, _t, n, d in rows:
            if rx.search(f"{n} {d}"):
                hit.setdefault(n, (s, d))
                srv.add(s)
        matches[fam] = hit
        say(f"{fam:18s}{len(hit):>8}/{len(names):<6}{len(srv):>4}/{len(servers):<4}")

    say("\nEVERY match, so the coarse rule can be audited rather than trusted:")
    for fam, hit in matches.items():
        if not hit:
            say(f"  {fam:18s} (none)")
            continue
        for n, (s, d) in sorted(hit.items()):
            say(f"  {fam:18s} {s}/{n}: {d[:66]}")
    say("\nAudit note, by inspection: every `operator/tenant` match is repository")
    say("ownership in GitHub/Codacy tooling, not the tenant an agent is deployed")
    say("for. Semantically the deployment-tenancy count is 0, not 5. The rule is")
    say("left coarse and unchanged so it stays reproducible; the correction lives")
    say("here rather than in a tuned regex.")

    text = "\n".join((s.get("clean_system_promot") or "") for s in servers.values())
    say("\n" + "=" * 74)
    say("VICTIM SURFACE — does real MCP host-prompt text carry what we plant?")
    say("=" * 74)
    for k, p in VICTIM_PROBES.items():
        n = len(re.findall(p, text))
        say(f"  {k:18s} {n:>4} occurrence(s) in {len(text):,} chars of host prompt")
    victim = {k: len(re.findall(pr, text)) for k, pr in VICTIM_PROBES.items()}
    say("\nSCOPE, and it cuts against us: these prompts are MCPTox's constructed")
    say("tool listings, not deployment prompts from a shipped agent product. They")
    say("bound what a HOST puts in front of a model in this corpus; they say")
    say("nothing about what Cursor or Claude Desktop put in theirs. Severity")
    say("therefore remains scoped to deployments whose prompts carry such")
    say("material, and that population is still unmeasured.")

    return {
        "servers": len(servers), "params": len(rows), "distinct_names": len(names),
        "attack": {fam: {"names": len(hit),
                         "servers": len({s for s, _t, n, d in rows
                                         if re.compile(FAMILY_RULES[fam]).search(f"{n} {d}")})}
                   for fam, hit in matches.items()},
        "victim": victim, "victim_chars": len(text),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--prevalence", action="store_true",
                    help="measure attack-surface plausibility and victim-surface content")
    args = ap.parse_args()
    if args.prevalence:
        prevalence(offline=True)
        return

    print("harvesting S1 (MCPTox, 45 live MCP servers)…")
    s1 = harvest_mcptox(args.offline)
    print("harvesting S2 (OpenTelemetry semantic conventions)…")
    s2 = harvest_otel(args.offline)
    fields = s1 + s2

    # The corpus MUST contain the hard case, or the FP number is meaningless.
    hard = [f for f in fields
            if re.search(r"(user_?agent|service\.name|telemetry\.sdk|client\.)",
                         f["name"], re.I)]
    if not hard:
        raise SystemExit("corpus is missing client-identity fields — the hardest "
                         "negatives; refusing to write a misleading FP corpus")

    payload = {
        "_provenance": {
            "generated_by": "harvest_benign_fields.py",
            "s1_mcptox": {"url": MCPTOX_URL, "n": len(s1),
                          "note": "clean tool schemas only; poisoned definitions never read"},
            "s2_otel": {"base": OTEL_BASE, "registries": OTEL_REGISTRIES, "n": len(s2),
                        "note": "hard negatives: legitimate caller-describing telemetry"},
            "hard_negatives_present": len(hard),
            "excluded": "request_trace_id — it is condition D, an experimental "
                        "control, not an independent benign field",
        },
        "fields": fields,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"\nS1 mcptox: {len(s1)}   S2 otel: {len(s2)}   total: {len(fields)}")
    print(f"hard client-identity negatives: {len(hard)}")
    for h in hard[:10]:
        print(f"   {h['name']:32s} {h['desc'][:60]}")
    print(f"-> {OUT}")
    if len(fields) < 100:
        print("WARNING: fewer than 100 benign fields; FP estimate will be coarse",
              file=sys.stderr)


if __name__ == "__main__":
    main()
