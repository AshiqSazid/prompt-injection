"""
manifest.py — one immutable source for every headline number, plus a checker that
catches stale numbers in prose.

WHY THIS EXISTS. Both USENIX-style reviews of this project independently flagged
the same failure: the README advertised "87-100%" and a broad benign-over-explicit
inversion while the consolidated results reported different pooled values, and the
threat model quoted 87% for a cell the abstract quoted at 97%. A reviewer reads
that as an unstable claim surface and starts doubting numbers that are in fact
correct.

`make_tables.py` already regenerates the TABLES from artifacts. This closes the
other half: the numbers that appear in PROSE. Every claim registered here is
computed from runs/ at check time, so a claim cannot drift from its evidence
without the check failing.

    python manifest.py            # print the manifest
    python manifest.py --write    # -> data/results_manifest.json
    python manifest.py --check    # fail if prose contradicts the manifest

The checker is deliberately narrow: it verifies REGISTERED claims (a phrase plus
the number that must accompany it) rather than trying to parse every percentage in
every document. A check that fires on ordinary prose gets deleted; one that guards
the load-bearing claims survives.
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

import analyze
import conditions
import evidence
from analyze import _field_args, _norm, canonical_runs, wilson

OUT = "data/results_manifest.json"

GATE = {
    "gpt-4o": "runs/v4-apidoc-gate.jsonl",
    "claude-sonnet-4-5": "runs/gate_anthropic_apidoc-live-20260726-182359.jsonl",
    "gemini-3-flash": "runs/gate_google_apidoc-live-20260801-200257.jsonl",
}
REPLICATE = [("runs/v4-apidoc-gate.jsonl", "cursor"),
             ("runs/confound_fix_openai-live-20260726-232559.jsonl", None)]


def _rows(path, framework=None):
    if not os.path.exists(path):
        raise FileNotFoundError(f"required evidence missing: {path}")
    out = []
    rows = evidence.read_jsonl(path)
    evidence.validate_trials(rows, path)
    for r in rows:
        if "error" in r:
            continue
        if framework is not None and r.get("framework") != framework:
            continue
        out.append(r)
    return out


def _cell(rows, cond):
    sub = [r for r in rows if r["condition"] == cond]
    if conditions.NEEDS_TOOL.get(cond):
        sub = [r for r in sub if r.get("tool_called")]
    return sum(1 for r in sub if r["tier_flags"]["T1"]), len(sub)


def build():
    """Every number the prose is allowed to quote, derived at run time."""
    m = {}
    for entry in evidence.selection():
        if not os.path.isfile(entry["path"]) or evidence.digest(entry["path"]) != entry["sha256"]:
            raise ValueError(f"missing or changed selected artifact: {entry['path']}")

    # 1. Gate, scaffolded arm.
    for model, path in GATE.items():
        rows = _rows(path, "cursor")
        if not rows:
            continue
        for cond in ("A", "A_prime", "B", "C", "D"):
            k, n = _cell(rows, cond)
            m[f"gate.{model}.{cond}"] = {"k": k, "n": n, "pct": round(100 * k / n) if n else None}
        # The pre-registered decision quantity itself. Without it the manuscript
        # had to print `C% - A'%` and leave the subtraction to the reader, which
        # is a results table showing its working instead of its result.
        # Unsigned on purpose: every observed value is >= 0, and "+0 pp" reads as
        # a claim about direction that a zero does not support.
        c, a = m[f"gate.{model}.C"]["pct"], m[f"gate.{model}.A_prime"]["pct"]
        if c is not None and a is not None:
            m[f"gate.{model}.delta"] = {"pp": c - a}

    # 2. The pooled replicate cell -- the one two documents disagreed about.
    for cond in ("A_prime", "C"):
        k = n = 0
        for path, fw in REPLICATE:
            a, b = _cell(_rows(path, fw), cond)
            k += a
            n += b
        p, lo, hi = wilson(k, n)
        m[f"pooled.gpt-4o.{cond}"] = {"k": k, "n": n, "pct": round(100 * p),
                                      "ci": [round(100 * lo), round(100 * hi)]}

    # 3. Real-schema arm, trial level and tool level.
    for label, pat in (("gpt-4o", "runs/real_schemas_openai-live-*.jsonl"),
                       ("claude-sonnet-4-5", "runs/real_schemas_anthropic-live-*.jsonl")):
        hits = canonical_runs(pat)
        if not hits:
            continue
        rows = _rows(hits[-1])
        for cond in ("C", "D"):
            k, n = _cell(rows, cond)
            tools = {}
            for r in rows:
                if r["condition"] == cond and r.get("tool_called"):
                    t = tools.setdefault(r["tool_offered"], [0, 0])
                    t[1] += 1
                    t[0] += bool(r["tier_flags"]["T1"])
            # ITT denominator is EVERY successful trial, not only the ones that
            # produced a tool call. Registered because the method section promises
            # an intention-to-treat figure beside every conditional rate, and for
            # three drafts there was no macro to honour that with.
            itt_n = sum(1 for r in rows if r["condition"] == cond)
            m[f"real.{label}.{cond}"] = {
                "k": k, "n": n, "pct": round(100 * k / n) if n else None,
                "itt_k": k, "itt_n": itt_n,
                "itt_pct": round(100 * k / itt_n) if itt_n else None,
                "tools_leaking": sum(1 for v in tools.values() if v[0] > 0),
                "tools_called": len(tools)}

    # 3b. Corpus size, which is NOT the same number as tools-called and has been
    # confused with it twice. The corpus is 25 tools from 25 servers; 24 is how
    # many gpt-4o actually invoked under condition C. Registering it separately
    # so the manuscript cannot reach for the wrong macro.
    if os.path.exists("data/real_tools.json"):
        with open("data/real_tools.json", encoding="utf-8") as f:
            rt = json.load(f)
        m["real.corpus"] = {"tools": len(rt["tools"]),
                            "servers": len(rt["_provenance"]["servers"])}

    # 4. Neutral-field floor, combined across providers -- quoted as "0/228".
    k = n = 0
    for pat in ("runs/real_schemas_openai-live-*.jsonl",
                "runs/real_schemas_anthropic-live-*.jsonl"):
        hits = canonical_runs(pat)
        if hits:
            a, b = _cell(_rows(hits[-1]), "D")
            k += a
            n += b
    m["real.D.combined"] = {"k": k, "n": n}

    # 4b. Condition E -- prior work's EXPLICIT parameters (`system_prompt`,
    # `model_name`), scored by marker recovery rather than T1. Registered because
    # the related-work section claims this arm "supplies the first measured
    # numbers" for HiddenLayer, and for three drafts the paper made that claim
    # without printing a single one of them.
    #
    # CARRY THE CONFOUND WHEREVER THESE ARE QUOTED (CLAUDE.md §6.2, §15.11): the
    # v1 payload fixtures are not matched on confidentiality-instruction strength,
    # and `credential_shaped` tells the model IN THE PROMPT that the credential is
    # "(test fixture, not a live credential)" -- so its rate measures the
    # annotation as much as the channel. LOOSE is the reported column: User-Agent
    # concatenation and partial disclosure are real leaks that STRICT misses.
    e_hits = canonical_runs("runs/explicit_payloads_openai-live-*.jsonl")
    if e_hits:
        e_rows = _rows(e_hits[-1])
        groups = {}
        for r in e_rows:
            groups.setdefault(r.get("framework", "?"), []).append(r)
        tot_k = tot_n = 0
        for fw, rs in groups.items():
            scored = analyze.payload_recovery(rs, fw.replace("payload_", ""))
            if scored is None:
                continue
            _strict, loose, _any, _calls, n = scored
            m[f"explicit.gpt-4o.{fw.replace('payload_', '')}"] = {
                "k": loose, "n": n, "pct": round(100 * loose / n) if n else None}
            tot_k += loose
            tot_n += n
        if tot_n:
            m["explicit.gpt-4o.pooled"] = {
                "k": tot_k, "n": tot_n, "pct": round(100 * tot_k / tot_n)}

    # 5. Framework arm -- the retraction.
    k = n = called = 0
    for pat in ("runs/framework_arm_openai-live-20260727-002409.jsonl",
                "runs/framework_arm_anthropic-live-20260727-002821.jsonl"):
        rows = _rows(pat)
        n += len(rows)
        called += sum(1 for r in rows if r.get("tool_called"))
        k += sum(1 for r in rows if r["tier_flags"]["T1"])
    m["framework_arm"] = {"disclosed": k, "n": n, "tool_called": called}

    # 6. protocol-v2 matrix (EXPLORATORY — protocol-v2.md was never committed).
    #
    # Three filters, and every one of them is load-bearing. Without the condition
    # filter the neutral control (D) enters the diagonal denominator -- D rows
    # inherit the stage's `wording_style` -- and the diagonal reads 50% instead of
    # 99%. That exact bug was fixed twice elsewhere (analyze.matrix_report,
    # stats.report_cluster) and survived here, registering a wrong number in the
    # file whose entire job is to be the authoritative one.
    hits = [h for h in canonical_runs("runs/v2_matrix*-live-*.jsonl")
            if "probe" not in os.path.basename(h)]
    if hits:
        rows = []
        for h in hits:
            rows += [r for r in _rows(h)
                     if r.get("condition") == "C"
                     and float(r.get("temperature", -1)) == 0.7]
        facts = conditions.OMNIBUS_FACTS
        tgt = conditions.V2_FIELD_TARGET
        for model in sorted({r["model"] for r in rows}):
            diag = off = dn = on_ = 0
            for ws, want in tgt.items():
                sub = [r for r in rows if r["model"] == model
                       and r.get("wording_style") == ws and r.get("tool_called")]
                if not sub:
                    continue
                for fkey, (marker, aliases) in facts.items():
                    hit = sum(1 for r in sub if any(
                        _norm(w) in _norm(_field_args(r)) for w in [marker] + aliases))
                    if fkey == want:
                        diag += hit; dn += len(sub)
                    else:
                        off += hit; on_ += len(sub)
            if dn:
                m[f"v2.{model}.diagonal"] = {"k": diag, "n": dn,
                                             "pct": round(100 * diag / dn)}
                m[f"v2.{model}.offdiagonal"] = {"k": off, "n": on_,
                                                "pct": round(100 * off / on_) if on_ else None}

    # 7. Detection (§9). Verdicts from the stored run of Invariant's published
    # policy, plus our own scanner in both profiles, computed live from the
    # schemas so the two can never disagree about which arm was tested.
    inv = "results/scan-invariant-policy.json"
    if os.path.exists(inv):
        with open(inv, encoding="utf-8") as f:
            blob = json.load(f)
        for arm, v in blob["results"].items():
            m[f"scan.invariant.{arm}"] = {"flagged": int(v["verdict"] != "clean")}
        m["scan.invariant.meta"] = {"reps": blob.get("reps", 0),
                                    "arms": len(blob["results"])}
    # The 2026-10-04 re-run keeps every raw reply, rejects malformed ones, and
    # adds the Study 1-4 fields (arms prefixed S1/, S2/, S3/, S4/). The journal
    # manuscript cites it under scan.raw.*; the historical boolean-only record
    # above stays registered unchanged, because the USENIX snapshot quotes it.
    # The -s4 file supersedes the first 2026-10-04 raw run and adds the ten
    # Study 4-only field texts (account_attribution among them).
    raw_path = "results/scan-invariant-policy-raw-20261004-s4.json"
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as f:
            blob = json.load(f)
        if any(v["verdict"] == "invalid" for v in blob["results"].values()):
            raise RuntimeError(f"{raw_path} holds invalid classifier observations")
        for arm, v in blob["results"].items():
            m[f"scan.raw.{arm}"] = {"flagged": int(v["verdict"] != "clean")}
        raw = [r for v in blob["results"].values() for r in v.get("raw_votes", [])]
        study = {k: v for k, v in blob["results"].items() if k.split("/")[0] in ("S1", "S2", "S3", "S4")}
        meta = {"reps": blob["_provenance"]["reps"], "arms": len(blob["results"]),
                "calls": len(raw), "valid": sum(r.get("content") in ("YES", "NO") for r in raw),
                "studyarms": len(study),
                "studyflagged": sum(v["verdict"] != "clean" for v in study.values())}
        for group, word in (("S1", "sone"), ("S2", "stwo"), ("S3", "sthree"), ("S4", "sfour")):
            mine = [v for k, v in study.items() if k.split("/")[0] == group]
            meta[word + "arms"] = len(mine)
            meta[word + "flagged"] = sum(v["verdict"] != "clean" for v in mine)
        m["scan.raw.meta"] = meta
    try:
        import scan
        for profile in ("desc", "descname"):
            res = scan.scan_conditions(profile="desc" if profile == "desc" else "desc+name")
            for cond, hits in res.items():
                m[f"scan.{profile}.{cond}"] = {"flagged": int(bool(hits))}
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError("required scanner analysis failed") from e

    # 8. Defense (§10). AUC and -- the number a deployer actually needs --
    # precision at realistic attack base rates.
    ev = "data/defense_eval.json"
    if os.path.exists(ev):
        import contextlib, io
        import defense
        with open(ev, encoding="utf-8") as f:
            d = json.load(f)
        pos = [x for x in d["fields"] if x["label"] == 1]
        neg = [x for x in d["fields"] if x["label"] == 0]
        # AUC is conventionally reported on 0--1, not as a percentage. Generate
        # the fixed-seed percentile interval from the same scored artifact; the
        # bootstrap helper is verbose for CLI use, so suppress its report here.
        with contextlib.redirect_stdout(io.StringIO()):
            auc_bootstrap = defense.bootstrap_auc(ev)
        m["defense.auc"] = {
            "value": round(d["auc"], 3),
            "ci": [round(x, 3) for x in auc_bootstrap["ci"]],
        }
        m["defense.corpus"] = {"positives": len(pos), "negatives": len(neg)}
        thr = 20
        tpr = sum(1 for x in pos if x["score"] >= thr) / len(pos)
        fpr = sum(1 for x in neg if x["score"] >= thr) / len(neg)
        m["defense.tpr.at20"] = {"pct": round(100 * tpr)}
        m["defense.fpr.at20"] = {"pct": round(100 * fpr, 1)}
        for prior, tag in ((0.001, "pointone"), (0.01, "one"), (0.05, "five")):
            m[f"defense.ppv.{tag}"] = {
                "pct": round(100 * defense.precision_at_prior(tpr, fpr, prior), 1)}
            m[f"defense.baserate.{tag}"] = {"pct": round(100 * prior, 1)}
        ua = next((x["score"] for x in pos if x["name"] == "client_user_agent"), None)
        legit = max((x["score"] for x in neg
                     if re.search(r"user_?agent", x["name"], re.I)), default=None)
        if ua is not None and legit is not None:
            m["defense.band"] = {"attack": ua, "legitimate": legit}

    # 8b. Depth factors (§10). These were quoted in prose as "60 pp" and "30 pp"
    # while living nowhere but a chat message -- the precise shape of drift this
    # file prevents. Registered so the manuscript cites a macro.
    dep = canonical_runs("runs/v2_depth_openai-live-*.jsonl")
    if dep:
        facts, tgt = conditions.OMNIBUS_FACTS, conditions.V2_FIELD_TARGET
        cells = {}
        for r in _rows(dep[-1]):
            if not r.get("tool_called"):
                continue
            marker, aliases = facts[tgt[r["wording_style"]]]
            c = cells.setdefault(r["framework"], [0, 0])
            c[1] += 1
            c[0] += any(_norm(w) in _norm(_field_args(r)) for w in [marker] + aliases)
        for arm, (k, n) in cells.items():
            # arm labels already begin with "depth_"; prefixing again yields
            # \DepthDepthUaOptional, which nobody will type correctly.
            m[f"depth.{arm.removeprefix('depth_')}"] = {"k": k, "n": n, "pct": round(100 * k / n) if n else None}
        # The delta must be against THAT FIELD's own required/after rate, not the
        # aggregate diagonal: the diagonal averages seven fields, so using it
        # reported the drop as 59/29 instead of 60/30. Compare like with like.
        base_rows = []
        for h in [x for x in canonical_runs("runs/v2_matrix_openai-live-*.jsonl")
                  if "probe" not in os.path.basename(x)]:
            base_rows += [r for r in _rows(h) if r.get("condition") == "C"
                          and float(r.get("temperature", -1)) == 0.7
                          and r.get("tool_called")]
        # posfirst is here for the same reason as optional: both are `protocol.md`
        # §4 depth factors, and the position arm is the one that came back NULL.
        # A null needs its baseline registered exactly as a positive result does,
        # or the manuscript has no macro with which to state "no effect".
        for arm, ws in (("depth_ua_optional", "api_documentation"),
                        ("depth_cred_optional", "m_credential"),
                        ("depth_ua_posfirst", "api_documentation"),
                        ("depth_cred_posfirst", "m_credential")):
            sub = [r for r in base_rows if r.get("wording_style") == ws]
            if arm not in cells or not sub:
                continue
            marker, aliases = facts[tgt[ws]]
            bk = sum(1 for r in sub
                     if any(_norm(w) in _norm(_field_args(r)) for w in [marker] + aliases))
            k, n = cells[arm]
            m[f"{arm}.baseline"] = {"k": bk, "n": len(sub),
                                    "pct": round(100 * bk / len(sub))}
            m[f"{arm}.drop"] = {"pct": round(100 * bk / len(sub) - 100 * k / n)}

    # 8b. R6 -- the content-familiarity contrast. POST-HOC, and it post-dates the
    # protocol-v3 witness. One model, one field, two arms differing only in
    # whether the planted platform canary is recognisable. Registered because it
    # FALSIFIES this project's own published explanation of the client_user_agent
    # discrepancy: we predicted the recognisable name would recover more readily,
    # and it recovers an order of magnitude less.
    try:
        hits = canonical_runs("runs/r6_familiarity_openai-live-*.jsonl")
        if hits:
            rows = _rows(hits[-1])
            for label, arm, key in (("familiar", "payload_v3_omnibus_familiar",
                                     "v3_omnibus_familiar"),
                                    ("seed", "payload_v3_omnibus", "v3_omnibus")):
                sub = [r for r in rows if r.get("framework") == arm
                       and r.get("tool_called")]
                marker = conditions.PAYLOADS[key][1]
                wanted = [marker] + analyze.PAYLOAD_ALIASES.get(key, [])
                k = sum(1 for r in sub if any(_norm(w) in _norm(_field_args(r))
                                              for w in wanted))
                m[f"r6.{label}"] = {"k": k, "n": len(sub),
                                    "pct": round(100 * k / len(sub)) if sub else None}
            if "r6.familiar" in m and "r6.seed" in m:
                m["r6.delta"] = {"pp": m["r6.seed"]["pct"] - m["r6.familiar"]["pct"]}
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError("required R6 analysis failed") from e

    # 9. Prevalence (§8). Ecological validity of both surfaces.
    try:
        import harvest_benign_fields as H
        pv = H.prevalence(offline=True, quiet=True)
        m["prevalence.corpus"] = {"servers": pv["servers"], "params": pv["params"],
                                  "n": pv["distinct_names"]}
        for fam, v in pv["attack"].items():
            m[f"prevalence.attack.{fam.replace('/', '')}"] = {
                "k": v["names"], "n": pv["distinct_names"], "servers": v["servers"]}
        for probe, n in pv["victim"].items():
            m[f"prevalence.victim.{probe.replace(chr(45), chr(0x2205)).replace(chr(47), chr(0x2205)).replace(chr(32), chr(0x2205)).replace(chr(0x2205), chr(0))}"] = {"k": n}
        m["prevalence.victim.chars"] = {"n": pv["victim_chars"]}
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError("required prevalence analysis failed") from e

    # 11b. The Sequential Thinking server. This is the paper's answer to its own
    # prevalence problem, so the counts belong in the manifest rather than in
    # prose: a widely-deployed, entirely legitimate MCP server asks agents to
    # report their own chain-of-thought -- one of the four exfiltration
    # parameters prior work published -- and its parameters false-positive at
    # our operating threshold. Derived from the same scored corpus as the ROC.
    try:
        ev = json.load(open("data/defense_eval.json", encoding="utf-8"))
        fps = [f for f in ev["fields"] if f["label"] == 0 and f["score"] >= 20]
        seq = [f for f in fps if "Sequential Thinking" in f.get("src", "")]
        m["defense.seqthinking"] = {"k": len(seq), "n": len(fps),
                                    "names": len({f["name"] for f in seq})}
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError("required defense analysis failed") from e

    # 12. protocol-v3 -- the confirmatory arm. Registered per model, and the
    # pre-registered pair is flagged so the manuscript cannot quietly report five
    # providers as confirmatory: `protocol-v3.md` §3 names gpt-4o and
    # gemini-3-flash-preview and nothing else. Everything here comes from
    # make_v3_report, which is the single implementation of the v3 scoring rules
    # -- duplicating them here is how the diagonal ends up defined twice.
    try:
        import make_v3_report as v3r
        mats = v3r.pick(v3r.canonical("runs/v3_matrix_*-live-*.jsonl"), v3r.matrix_stats)
        unpl = v3r.pick(v3r.canonical("runs/v3_unplanted_*-live-*.jsonl"), v3r.unplanted_stats)
        fab_k = fab_n = 0
        for d in mats:
            slug = d["model"].split("-2025")[0]
            for label, (k, n) in (("diagonal", d["diag"]), ("offdiag", d["off"]),
                                  ("control", d["ctrl"])):
                # protocol-v3's primary estimand generalises over fields.  Its
                # diagonal/off-diagonal intervals therefore come from the
                # paired field bootstrap computed by make_v3_report, not from a
                # Wilson interval that treats repeated calls as independent.
                if label in ("diagonal", "offdiag"):
                    which = "first" if label == "diagonal" else "second"
                    p_, lo, hi = d["cluster"][which]
                else:
                    p_, lo, hi = wilson(k, n) if n else (0, 0, 0)
                m[f"v3.{slug}.{label}"] = {"k": k, "n": n,
                                           "pct": round(100 * p_) if n else None,
                                           "ci": [round(100 * lo), round(100 * hi)]}
                if label == "control":
                    # Five correlated fact checks per call: no binomial event CI.
                    del m[f"v3.{slug}.{label}"]["ci"]
            ck, cn = d["ctrl_calls"]
            m[f"v3.{slug}.controlcalls"] = {"k": ck, "n": cn}
            delta, delta_lo, delta_hi = d["cluster"]["difference"]
            m[f"v3.{slug}.delta"] = {
                "pp": round(100 * delta),
                "ci": [round(100 * delta_lo), round(100 * delta_hi)],
                "clusters": d["clusters"],
            }
            generic_k, generic_n = d["generic"]
            m[f"v3.{slug}.generic"] = {
                "k": generic_k, "n": generic_n,
                "pct": round(100 * generic_k / generic_n) if generic_n else None,
            }
            for label, cls in (("naming", "naming"), ("adjacent", "adjacent")):
                k, n = d["by_class"].get(cls, (0, 0))
                p_, lo, hi = wilson(k, n) if n else (0, 0, 0)
                m[f"v3.{slug}.{label}"] = {"k": k, "n": n,
                                           "pct": round(100 * p_) if n else None,
                                           "ci": [round(100 * lo), round(100 * hi)]}
            k, n = d["per_field"].get("m_credential", (0, 0))
            m[f"v3.{slug}.credential"] = {"k": k, "n": n,
                                          "pct": round(100 * k / n) if n else None}
            # Per FIELD, not just per class. The aggregate hides the finding: the
            # adjacent class reads a uniform 33% on four models, but that is one
            # near-synonym field at 20/20 while the two genuinely non-naming
            # fields are 0/20. A table built from the aggregate would state the
            # opposite of what the data show.
            for wording, (fk, fn) in d["per_field"].items():
                m[f"v3.{slug}.field.{wording}"] = {
                    "k": fk, "n": fn,
                    "pct": round(100 * fk / fn) if fn else None}
            # WHERE the off-diagonal comes from. Pooled it is ~1% on every model
            # and reads as uniform noise; per field it is one broad-category
            # field spraying its neighbours while every fact-specific field is
            # exactly clean. Registered as counts of the model's own off-diagonal
            # so the manuscript states a share, not a second rate.
            off_tot = d["off"][0]
            ua = d["per_field_off"].get("api_documentation", (0, 0))[0]
            named = sum(d["per_field_off"].get(w, (0, 0))[0]
                        for w in ("m_region", "m_operator", "m_credential"))
            m[f"v3.{slug}.crosstalkua"] = {"k": ua, "n": off_tot}
            m[f"v3.{slug}.crosstalknaming"] = {"k": named, "n": off_tot}
        for d in unpl:
            slug = d["model"].split("-2025")[0]
            m[f"v3.{slug}.fabrication"] = {"k": d["canary"], "n": d["called"],
                                          "pct": round(100*d['canary']/d['called']) if d['called'] else None}
            fab_k += d["canary"]; fab_n += d["called"]
        m["v3.fabrication.pooled"] = {"k": fab_k, "n": fab_n,
                                       "pct": round(100*fab_k/fab_n) if fab_n else None}
        m["v3.primary"] = {"status": v3r.primary_decision(mats)}
        m["v3.providers"] = {"confirmatory": 2, "total": len(mats)}
        m["v3.trials"] = {"n": sum(d["attempted_rows"] for d in mats + unpl),
                           "errors": sum(d["errors"] for d in mats + unpl)}
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError("required v3 analysis failed") from e

    return m


# Registered prose claims: (file, regex that must match, manifest key, extractor).
# Each entry says "wherever this phrase appears, the number beside it must equal
# the manifest". Keep this list short and load-bearing.
# README numbers bound to the artifacts that produce them. Reword the README and
# these must be rewritten with it -- that is the point: --check fails rather than
# letting the prose drift silently. Keep the capture group on the number.
CLAIMS = [
    ("README.md", r"\*\*(\d+)%\*\* \[\d+, \d+\] pooled on gpt-4o for the\s+`client_user_agent`",
     "pooled.gpt-4o.C", "pct"),
    ("README.md", r"neutral-parameter floor of \*\*0/(\d+)\*\*", "real.D.combined", "n"),
    # The confirmatory result is now the headline, so it gets a binding too.
    ("README.md", r"\| `gpt-4o` \| \*\*confirmatory\*\* \| \*\*(\d+)%\*\*", "v3.gpt-4o.diagonal", "pct"),
    ("README.md", r"\*\*Unplanted control: 0/(\d+)\.\*\*", "v3.fabrication.pooled", "n"),
]

# Numbers that must NEVER appear in prose again, with the reason.
BANNED = [
    (r"87\s*[-–]\s*100%", "superseded: the pooled gpt-4o condition-C rate is "
                          "92% [82, 96]; '87-100%' mixed two runs of one cell"),
    # Paraphrase-tolerant. The original pattern matched "politeness beats
    # honesty" but not "Politeness outperforms both honesty and coercion", which
    # is the exact sentence that survived in RELATED_WORK.md for three rounds.
    (r"politeness\s+(?:beats|outperforms|wins over|defeats)",
     "withdrawn: the inversion holds only in reticent regimes"),
    (r"benign framing\s*(?:\(87[^)]*\))?\s*>\s*explicit ask",
     "withdrawn: the inversion ordering was measured on one model and is "
     "superseded by selectivity (docs/v6.md §3a)"),
    (r"bounded to identifier-shaped content",
     "WITHDRAWN by protocol-v2: the bound was a property of the one field being "
     "asked. The credential extracts 20/20 through a field that names it "
     "(docs/v6.md §3a)"),
    (r"fingerprinting-grade, not secret-exfiltration-grade",
     "withdrawn with the severity bound; see docs/v6.md §3a"),
    (r"zero[- ]cost (?:universal )?mitigation|universal .{0,20}mitigation",
     "withdrawn: rung 3 closes C on Claude but not on Gemini, and the classifier "
     "is not deployable at realistic base rates"),
    # The provenance failure. protocol-v2.md was never committed, so nothing may
    # describe the v2 result as confirmatory or as pre-committed. This is the
    # exact claim the checker missed the first time, because it was not
    # registered -- the reason it is registered now.
    (r"pre-commitment was made before the data|frozen before any (?:live )?"
     r"(?:data|`?v2_?\*?`? ?stage)|confirmatory (?:study|result)s? \(v2\)",
     "FALSE: protocol-v2.md was never committed; git shows no such ordering. The "
     "v2 results are exploratory (docs/DEVIATIONS.md §8a)"),
    (r"selects the exploit|precondition for targeting",
     "WITHDRAWN: the exploit-chain claim was never demonstrated. The paper claims "
     "an information-flow result, not a step in a kill chain "
     "(docs/THREAT_MODEL.md §4.1)"),
]
# docs/RELATED_WORK.md was on this list and should never have been. It is the
# section a PC judges novelty from, it asserted two withdrawn claims for three
# review rounds, and the exemption is why `--check` reported "0 prose problems"
# the whole time. A guard that skips the document most likely to be stale is
# decoration.
BANNED_SKIP = ("docs/archive/", "manifest.py", "docs/DEVIATIONS.md", "CLAUDE.md",
               "protocol.md", "protocol-v2.md",
               # Generated by --tex from the artifacts. Not prose, and nothing a
               # human writes, so there is no claim in them to go stale.
               "paper/numbers.tex", "paper/roc.tex")
# A line that tells the reader NOT to use a claim is not making the claim. Without
# this the checker flags its own deprecation notices, which is how a check that
# cries wolf ends up deleted.
_NEGATION = re.compile(
    # DELIBERATELY NARROW. An earlier version listed "rather than", "previously"
    # and "historical" -- phrases that occur constantly in ordinary prose, so any
    # banned claim within 160 characters of one was silently exonerated. That is
    # how an injected test claim passed while sitting two lines below the words
    # "credible rather than convenient". Only unambiguous deprecation markers
    # belong here.
    r"do not quote|don't quote|never quote|superseded|withdrawn|retracted|"
    r"no longer claim|banned claim|is stale|earlier claim|was an artifact|"
    r"falsified|this section is|claim is \*\*withdrawn", re.I)


LOCK = "usenix_paper/numbers.lock.json"


def macro_values(m):
    return dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", tex_content(m)))


def check_locations(m, paper="usenix_paper/main.tex", locations="data/manuscript_locations.json"):
    """Bind registered primary numbers to exact manuscript contexts, not global substrings."""
    values = macro_values(m)
    text = Path(paper).read_text(encoding="utf-8")
    entries = json.loads(Path(locations).read_text(encoding="utf-8"))["claims"]
    problems = []
    if m.get("v3.primary", {}).get("status") not in (None, "supported") and "satisfying H-v3-1" in text:
        problems.append(f"{paper}: positive H-v3-1 conclusion conflicts with fresh analysis")
    for entry in entries:
        matches = list(re.finditer(entry["pattern"], text, re.MULTILINE))
        if len(matches) != 1:
            problems.append(f"{paper}: expected exactly one location for {entry['id']}, found {len(matches)}")
            continue
        if len(matches[0].groups()) != len(entry["macros"]):
            problems.append(f"{paper}: malformed location specification for {entry['id']}")
            continue
        for got, name in zip(matches[0].groups(), entry["macros"]):
            if got != values.get(name):
                problems.append(f"{paper}: {entry['id']} / {name}: {got!r} != {values.get(name)!r}")
    return problems


def check_inlined(m, lock=LOCK, paper="usenix_paper/main.tex", numbers="paper/numbers.tex",
                  locations="data/manuscript_locations.json"):
    """Report every number that has drifted out from under the flattened bundle.

    usenix_paper/main.tex carries literal numbers instead of \\input macros, by
    request. That trades away the one property the macros bought: a number in
    that file can now go stale when runs/ changes, silently, which is the exact
    failure this project has already corrected four times.

    The lock file records what each macro's value was at the moment it was
    inlined. If the registry no longer agrees, the manuscript is stale and the
    fix is a hand edit -- so we print old -> new rather than a bare complaint,
    because a checker that says 'something moved' without saying what costs more
    than it saves."""
    if not (os.path.exists(lock) and os.path.exists(paper)):
        return ["missing manuscript or numeric lock"]
    snapshot = json.loads(Path(lock).read_text(encoding="utf-8"))
    was = snapshot.get("values", snapshot)
    now = macro_values(m)
    out = []
    if not os.path.exists(numbers) or Path(numbers).read_text(encoding="utf-8") != tex_content(m):
        out.append(f"{numbers}: generated cache differs from fresh artifact calculations")
    if snapshot.get("manuscript_sha256") != evidence.digest(paper):
        out.append(f"{paper}: manuscript changed since audited lock; review and explicitly re-lock")
    for name, old_v in sorted(was.items()):
        new_v = now.get(name)
        if new_v != old_v:
            out.append(f"{paper}: {name} was {old_v!r}, runs/ now say {new_v!r} "
                       "(fresh computation)")
    out.extend(check_locations(m, paper, locations))
    return out


def check(m):
    problems = []
    for path, pattern, key, field in CLAIMS:
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        found = re.search(pattern, text)
        if not found:
            problems.append(f"{path}: registered claim not found: /{pattern}/")
            continue
        want = m.get(key, {}).get(field)
        got = int(found.group(1))
        if want is None:
            problems.append(f"{path}: manifest has no {key}.{field} to check against")
        elif got != want:
            problems.append(f"{path}: claims {got} but artifacts say {want} "
                            f"({key}.{field})")
    # SCAN THE MANUSCRIPTS TOO. This glob was `*.md` + `docs/**/*.md` for three
    # drafts, which left paper/main.tex -- the one file that actually gets
    # submitted -- as the only prose in the repository the guard never read.
    # Registered NUMBERS were safe there by construction, because the paper
    # quotes macros rather than digits, but a withdrawn CLAIM could reappear in
    # the submission unchallenged. The comment above BANNED_SKIP already says a
    # guard that skips the document most likely to be stale is decoration; that
    # was true of this checker itself.
    for path in sorted(glob.glob("*.md") + glob.glob("docs/**/*.md", recursive=True)
                       + glob.glob("*.tex") + glob.glob("paper/*.tex")
                       + glob.glob("usenix_paper/*.tex")):
        path = Path(path).as_posix()   # glob yields backslashes on Windows
        if any(path.startswith(s) or path == s for s in BANNED_SKIP):
            continue
        raw = open(path, encoding="utf-8").read()
        # Match over the WHOLE document with whitespace normalised, not line by
        # line. This repo wraps prose at ~80 characters, so a line-based check
        # silently missed every banned phrase that straddled a wrap -- e.g.
        # "bounded to identifier-shaped\ncontent" sat in RELATED_WORK.md while
        # the checker reported zero problems. Offsets map back to line numbers.
        flat, offsets, pos = [], [], 0
        for i, line in enumerate(raw.split("\n"), 1):
            flat.append(line)
            offsets.append((pos, i))
            pos += len(line) + 1
        text = "\n".join(flat)
        norm = re.sub(r"\s+", " ", text)
        # offset map for the normalised string: walk both in step
        nmap, j = [], 0
        for ch_i, ch in enumerate(text):
            if ch.isspace():
                if j and norm[j - 1] == " ":
                    continue
            nmap.append(ch_i)
            j += 1
        for pattern, why in BANNED:
            for mt in re.finditer(pattern, norm, re.I):
                orig = nmap[mt.start()] if mt.start() < len(nmap) else 0
                line_no = next((ln for off, ln in reversed(offsets) if off <= orig), 1)
                # A passage that tells the reader NOT to use a claim is not
                # making it. Scope the exemption to the PARAGRAPH containing the
                # match: a fixed character window either misses a deprecation
                # notice at the top of a long bullet, or exonerates a real claim
                # because an unrelated one sits nearby. Paragraphs are the unit
                # authors actually write deprecations in.
                para_start = text.rfind("\n\n", 0, orig) + 2
                para_end = text.find("\n\n", orig)
                para = text[para_start:para_end if para_end != -1 else len(text)]
                if _NEGATION.search(re.sub(r"\s+", " ", para)):
                    continue
                problems.append(f"{path}:{line_no}: asserts banned claim "
                                f"/{pattern}/ — {why}")
    return problems


_DIGIT = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
          "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}


def _macro(key):
    """manifest key -> a legal LaTeX control sequence.

    TeX macro names are letters only, so digits become words: `gate.gpt-4o.C`
    becomes `\\GateGptFourOC`. Ugly, and correct — a macro that silently fails to
    parse is worse than a verbose one."""
    out = []
    for part in re.split(r"[^A-Za-z0-9]+", key):
        if not part:
            continue
        out.append("".join(_DIGIT.get(ch, ch) for ch in part).capitalize()
                   if part.islower() or part.isdigit()
                   else "".join(_DIGIT.get(ch, ch) for ch in part))
    return "".join(out)


def tex_content(m):
    """Every number the manuscript is allowed to state, as LaTeX macros.

    THE POINT: the paper must not contain a hand-typed figure. `\\input` this and
    write `\\GateGptFourOC` instead of `29/30`, and a number can never drift from
    the artifact that produced it -- the failure this project has already had to
    correct in prose four times. Regenerate as a build step, not by hand."""
    lines = ["% GENERATED by manifest.py --tex -- DO NOT EDIT.",
             "% Every macro below is derived from runs/ at generation time.",
             "% Regenerate:  python manifest.py --tex", ""]
    # EXHAUSTIVE: every registered scalar becomes a macro. An earlier version
    # emitted only k/n/pct/ci plus a hard-coded extras list, which silently
    # dropped `defense.band`, every `scan.*` verdict and the victim-surface
    # counts -- so those numbers would have had to be typed into the manuscript
    # by hand, which is the one thing this file exists to prevent.
    emitted = set()

    def add(macro, value):
        if macro not in emitted:
            emitted.add(macro)
            lines.append(f"\\newcommand{{\\{macro}}}{{{value}}}")

    for key in sorted(m):
        v, name = m[key], _macro(key)
        if "k" in v and "n" in v:
            add(f"{name}Frac", f"{v['k']}/{v['n']}")
        if v.get("pct") is not None:
            add(f"{name}Pct", f"{v['pct']}\\%")
        if "ci" in v:
            add(f"{name}CI", f"[{v['ci'][0]}, {v['ci'][1]}]")
        # A k/n pair nested under a prefix (itt_k/itt_n) gets its own Frac macro,
        # so the manuscript can print an intention-to-treat rate without
        # assembling one from two macros and a slash.
        for pre in {f.rsplit("_", 1)[0] for f in v if f.endswith("_k")}:
            if f"{pre}_n" in v:
                add(f"{name}{_macro(pre)}Frac", f"{v[f'{pre}_k']}/{v[f'{pre}_n']}")
        for field, val in v.items():
            if field in ("pct", "ci") or not isinstance(val, (int, float)):
                continue
            # ANY field naming a percentage carries its sign. `itt_pct` emitted a
            # bare `62` while `pct` emitted `62\%`, which is a paper printing a
            # rate as if it were a count -- silent, and wrong in the direction
            # that flatters us.
            if field.endswith("pct"):
                add(f"{name}{_macro(field)}", f"{val}\\%")
                continue
            add(f"{name}{_macro(field)}", f"{val:,}" if val >= 10000 else val)
    return "\n".join(lines) + "\n"


def emit_tex(m, path="paper/numbers.tex"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = tex_content(m)
    open(path, "w", encoding="utf-8").write(content)
    lines = content.splitlines()
    print(f"{sum(1 for l in lines if l.startswith(chr(92) + 'newcommand'))} macros "
          f"-> {path}")


_FB_BEGIN = "% BEGIN GENERATED FALLBACK SNAPSHOT"
_FB_END = "% END GENERATED FALLBACK SNAPSHOT"


def sync_fallback(numbers="paper/numbers.tex",
                  # usenix_paper/main.tex is NOT here: its numbers were
                  # flattened to literal text by request, so it has no snapshot
                  # block to refresh. check_inlined() below is what guards it.
                  targets=("IEEE.tex", "paper/main.tex")):
    """Refresh each manuscript's provide-only snapshot from the generated macros.

    WHY THIS IS CODE AND NOT COPY-PASTE: a manuscript uploaded to a submission
    system without its generated siblings dies on `\\input{numbers}` before it
    typesets a line -- which is exactly how this was found. The snapshot keeps
    the upload compilable. But a snapshot maintained by hand is a second place
    every number lives, and this project has already corrected four numbers that
    drifted from their artifact. So it is generated, into both files, from the
    one file that is itself generated from runs/.

    Only macros the manuscript actually references are emitted, so the block
    tracks the prose rather than dumping the whole registry."""
    src = open(numbers, encoding="utf-8").read()
    defs = dict(re.findall(r"\\newcommand\{\\(\w+)\}\{(.*)\}", src))
    for path in targets:
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        if _FB_BEGIN not in text or _FB_END not in text:
            print(f"  [no fallback markers in {path}; skipped]", file=sys.stderr)
            continue
        head, rest = text.split(_FB_BEGIN, 1)
        _, tail = rest.split(_FB_END, 1)
        # Which macros does the PROSE use? Everything outside the block itself.
        used = set(re.findall(r"\\([A-Z][A-Za-z]+)", head + tail)) & set(defs)
        body = "\n".join(f"\\providecommand{{\\{n}}}{{{defs[n]}}}"
                         for n in sorted(used))
        note = ("\n% Source: paper/numbers.tex, restricted to macros this "
                "manuscript references.\n")
        open(path, "w", encoding="utf-8").write(
            head + _FB_BEGIN + note + body + "\n" + _FB_END + tail)
        print(f"{len(used)} fallback macros -> {path}")


def emit_roc(path="paper/roc.tex"):
    """The ROC curve as a LaTeX `picture` -- no TikZ, no pgfplots, no image file.

    The paper described a curve it never drew. Neither plotting package is
    installed here and adding one would make the manuscript unbuildable on a
    machine that lacks it, which is the failure the clone test just caught for
    the bibliography. `picture` and `\\qbezier` are LaTeX2e core, so this
    compiles anywhere the paper does, and it regenerates from
    data/defense_eval.json like every other number."""
    ev = json.load(open("data/defense_eval.json", encoding="utf-8"))
    pts = [(f, t) for f, t, _thr in ev["roc"]]
    if (0.0, 0.0) not in pts:
        pts.insert(0, (0.0, 0.0))
    if (1.0, 1.0) not in pts:
        pts.append((1.0, 1.0))
    S = 100                                   # unit box, in \unitlength
    xy = [(round(f * S, 1), round(t * S, 1)) for f, t in pts]
    L = [r"% GENERATED by manifest.py --tex -- DO NOT EDIT.",
         r"\setlength{\unitlength}{0.8pt}",
         r"\begin{picture}(120,120)(-12,-12)",
         r"  \put(0,0){\line(1,0){100}}",
         r"  \put(0,0){\line(0,1){100}}",
         r"  \multiput(0,0)(10,10){11}{\circle*{0.6}}",   # chance diagonal
         r"  \put(-10,-9){\scriptsize 0}",
         r"  \put(97,-9){\scriptsize 1}",
         r"  \put(-10,97){\scriptsize 1}",
         r"  \put(35,-11){\scriptsize false positive rate}",
         r"  \put(-9,40){\rotatebox{90}{\scriptsize true positive rate}}"]
    for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
        if (x1, y1) == (x2, y2):
            continue                          # draws nothing; \circle* marks it
        # ALWAYS PASS AN EXPLICIT POINT COUNT. Bare `\qbezier` derives its own
        # from the curve's extent, and on a short segment that derivation
        # overflows `\@multicnt` -- "! Arithmetic overflow", from a generated
        # figure nobody edits by hand. `article` tolerated the same file that
        # killed `IEEEtran`, so the automatic path is not merely fragile, it is
        # fragile per template. Computing N here makes the output identical
        # under any class.
        #
        # ROUND THE CONTROL POINT too: an unrounded midpoint such as
        # 11.649999999999999 overflows the same arithmetic for its own reason.
        cx, cy = round((x1 + x2) / 2, 2), round((y1 + y2) / 2, 2)
        span = abs(x2 - x1) + abs(y2 - y1)    # in \unitlength (0.8pt)
        n = min(200, max(2, int(1.6 * span)))  # ~0.5pt between dots
        L.append(f"  \\qbezier[{n}]({x1},{y1})({cx},{cy})({x2},{y2})")
    for x, y in xy:
        L.append(f"  \\put({x},{y}){{\\circle*{{1.6}}}}")
    L.append(r"\end{picture}")
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"ROC picture -> {path}")


# ---- appended to manifest.py by the figure work; keep beside emit_roc ----

# The five models, in the order the paper reports them: the two the witnessed
# protocol named, then the three added afterwards. Short codes because a model id
# does not fit a 20pt column header; the caption expands them.
_FIG_MODELS = [("gpt-4o", "4o", True),
               ("gemini-3-flash-preview", "G3F", True),
               ("claude-sonnet-4-5", "C45", False),
               ("deepseek-v4-flash", "DS4", False),
               ("gemini-3.1-pro-preview", "G3P", False)]

# Fields in the order \S{gradient} argues them: the two that genuinely avoid
# naming their target first, then the near-synonym that carries the whole pooled
# "adjacent" rate, then the naming fields.
_FIG_FIELDS = [("g_platform_adjacent", r"\texttt{issuing\_surface}", "adj"),
               ("g_credential_adjacent", r"\texttt{integration\_binding\_note}", "adj"),
               ("g_region_adjacent", r"\texttt{locality\_hint}", "adj"),
               ("api_documentation", r"\texttt{client\_user\_agent}", "nam"),
               ("m_region", r"\texttt{deployment\_region\_code}", "nam"),
               ("m_operator", r"\texttt{operator\_account\_name}", "nam"),
               ("m_credential", r"\texttt{service\_key\_reference}", "nam")]

_FIG_BEGIN = "% BEGIN GENERATED FIGURE: "
_FIG_END = "% END GENERATED FIGURE: "


def _fig_matrix(m):
    """Diagonal vs off-diagonal recovery per model, as a LaTeX `picture`.

    Same constraint as emit_roc: `picture` and `\\rule` are LaTeX2e core, so this
    compiles on a machine with neither TikZ nor pgfplots -- which is the machine
    the clone test runs on. \\unitlength is 1pt so every coordinate below reads
    directly against the 240pt USENIX column."""
    SCALE, X0, XVAL = 1.05, 62, 208   # 100% -> 105pt; value labels in a fixed
    ROW, BAR = 21, 6                  # right-hand column, never chasing the bar
    AXIS = 17                         # axis line height; title and ticks below it
    top = AXIS + len(_FIG_MODELS) * ROW
    L = [r"\setlength{\unitlength}{1pt}%",
         # Box must clear the TOP ROW'S WHISKER, not just its bar. Inside the
         # manuscript the float's own leading hid the overflow; cropped to the
         # picture box for export, the interval was sliced off mid-tick.
         r"\begin{picture}(232,%d)(0,0)" % (top + BAR + 10),
         r"  \put(%d,%d){\line(1,0){%d}}" % (X0, AXIS, round(100 * SCALE))]
    for pct in (0, 50, 100):
        x = X0 + pct * SCALE
        L.append(r"  \put(%.1f,%d){\line(0,1){3}}" % (x, AXIS))
        L.append(r"  \put(%.1f,%d){\makebox(0,0)[t]{\tiny %d}}" % (x, AXIS - 1, pct))
    L.append(r"  \put(%.1f,1){\makebox(0,0)[b]{\tiny canary recovery (\%%)}}"
             % (X0 + 50 * SCALE))
    for i, (model, short, conf) in enumerate(_FIG_MODELS):
        y = top - i * ROW
        # centred on the PAIR, not on either bar: the label names the model, and
        # sitting it level with one bar reads as labelling that bar alone.
        L.append(r"  \put(58,%d){\makebox(0,0)[l]{\makebox(0,0)[r]{\tiny %s%s}}}"
                 % (y + 1, short, r"\,$\bullet$" if conf else ""))
        for key, off, shade in (("diagonal", BAR + 2, "black"),
                                ("offdiag", 0, "black!30")):
            v = m.get(f"v3.{model}.{key}")
            if v is None or v.get("pct") is None:
                continue
            w, yb = max(0.4, v["pct"] * SCALE), y - BAR + off
            L.append(r"  \put(%d,%d){\textcolor{%s}{\rule{%.1fpt}{%dpt}}}"
                     % (X0, yb, shade, w, BAR))
            L.append(r"  \put(%d,%d){\makebox(0,0)[r]{\tiny %d\%%}}"
                     % (XVAL, yb + 1, v["pct"]))
            ci = v.get("ci")
            if ci and key == "diagonal":       # whisker on the headline bar only
                a, b = X0 + ci[0] * SCALE, X0 + ci[1] * SCALE
                yc = yb + BAR + 2
                L.append(r"  \put(%.1f,%d){\line(1,0){%.1f}}" % (a, yc, b - a))
                for e in (a, b):
                    L.append(r"  \put(%.1f,%d){\line(0,1){3}}" % (e, yc - 1))
    L.append(r"\end{picture}")
    return "\n".join(L)


def _fig_gradient(m):
    """Per-field recovery as a field x model grid of proportional-fill cells.

    A grid rather than grouped bars because the claim is about WHICH cells are
    empty: the two genuinely non-naming rows are blank everywhere except one
    quota-capped provider, and any averaging across the row states the opposite
    of the data (\\S gradient). A cell you can see is empty makes that unarguable."""
    CW, CH, GAP, X0 = 20, 7, 4, 116
    ROW = CH + 5
    foot = 10                                  # legend strip under the grid
    top = foot + len(_FIG_FIELDS) * ROW
    L = [r"\setlength{\unitlength}{1pt}%",
         r"\begin{picture}(232,%d)(0,0)" % (top + 10)]
    for j, (_model, short, conf) in enumerate(_FIG_MODELS):
        x = X0 + j * (CW + GAP)
        L.append(r"  \put(%d,%d){\makebox(%d,0)[b]{\tiny %s%s}}"
                 % (x, top + 3, CW, short, r"\,$\bullet$" if conf else ""))
    for i, (field, label, cls) in enumerate(_FIG_FIELDS):
        y = top - i * ROW
        bold = cls == "adj" and field != "g_region_adjacent"
        name = r"\textbf{%s}" % label if bold else label
        L.append(r"  \put(110,%d){\makebox(0,0)[l]{\makebox(0,0)[r]{\tiny %s}}}"
                 % (y - CH + 1, name))
        for j, (model, _short, _conf) in enumerate(_FIG_MODELS):
            x, v = X0 + j * (CW + GAP), m.get(f"v3.{model}.field.{field}")
            L.append(r"  \put(%d,%d){\framebox(%d,%d){}}" % (x, y - CH, CW, CH))
            if v is None or v.get("pct") is None:
                continue
            if v["pct"]:
                L.append(r"  \put(%d,%d){\rule{%.1fpt}{%dpt}}"
                         % (x, y - CH, v["pct"] / 100 * CW, CH))
            # A SHORT DENOMINATOR, from either of two causes: a quota wall
            # (gemini-3.1-pro, n=3) or the model declining to call the tool
            # (deepseek m_operator, n=17, in a stage that ran 320/320 with no
            # errors). Both make the cell a weaker estimate than its neighbours
            # and neither should read as a rate measured over the full cell --
            # but they are NOT the same thing, so the caption names both rather
            # than blaming the quota for a conditional-denominator effect.
            if v.get("n", 20) < 20:
                L.append(r"  \put(%d,%d){\makebox(%d,%d){\tiny $\ast$}}"
                         % (x, y - CH, CW, CH))
    L.append(r"  \put(%d,2){\makebox(0,0)[l]{\tiny empty $=$ never recovered}}" % X0)
    L.append(r"  \put(%d,2){\makebox(0,0)[r]{\tiny full $=$ every trial}}"
             % (X0 + 5 * CW + 4 * GAP))
    L.append(r"\end{picture}")
    return "\n".join(L)


def sync_figures(m, outdir="figures/src"):
    """Write each generated picture to its own source file under figures/src/.

    The manuscript includes a rendered PNG rather than the drawing code, so this
    writes the SOURCE and make_figures.py renders it. Earlier this spliced the
    body straight into main.tex; that stopped being viable the moment main.tex
    began including images, because make_figures.py read its bodies back out of
    main.tex and would have been consuming its own output.

    These pictures encode measured rates, so a hand-edited bar is a hand-typed
    number wearing a costume. Regenerate; never edit figures/src/matrix.tex or
    figures/src/gradient.tex by hand."""
    if not os.path.isdir(outdir):
        return
    for name, body in (("matrix", _fig_matrix(m)), ("gradient", _fig_gradient(m))):
        path = os.path.join(outdir, f"{name}.tex")
        open(path, "w", encoding="utf-8").write(
            "% GENERATED by manifest.py --tex -- DO NOT EDIT.\n"
            "% width: columnwidth\n" + body + "\n")
        print(f"figure source -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tex", action="store_true",
                    help="emit paper/numbers.tex so the manuscript never hand-types a number")
    ap.add_argument("--lock-inlined", action="store_true",
                    help="explicitly acknowledge a reviewed literal manuscript after location checks")
    a = ap.parse_args()
    m = build()
    if a.lock_inlined:
        problems = check_locations(m)
        if problems:
            raise SystemExit("\n".join(problems))
        with open(LOCK, "w", encoding="utf-8") as stream:
            json.dump({"schema_version": 2, "manuscript_sha256": evidence.digest("usenix_paper/main.tex"),
                       "values": macro_values(m),
                       "coverage": "Primary locations checked; remaining literal prose guarded by whole-file digest, not semantic verification"}, stream, indent=2)
        return
    if a.tex:
        emit_tex(m)
        emit_roc()
        sync_figures(m)
        # Both manuscripts carry a provide-only copy so an upload without the
        # generated files still compiles. Refreshed here, never by hand.
        sync_fallback()
        return
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=1, sort_keys=True)
        print(f"{len(m)} claims -> {OUT}")
        return
    if a.check:
        problems = check(m) + check_inlined(m)
        for p in problems:
            print(f"  STALE: {p}")
        print(f"\n{len(m)} registered numbers, {len(problems)} prose problem(s)")
        sys.exit(1 if problems else 0)
    for k in sorted(m):
        print(f"  {k:36s} {json.dumps(m[k])}")
    print(f"\n{len(m)} numbers, all derived from runs/ at run time.")
    print("Prose must agree: python manifest.py --check")


if __name__ == "__main__":
    main()
