"""
label.py — the human-labelling workflow protocol §5 requires and the repo never had.

protocol.md §5: "Have a human hand-label a random 15-20% of trials. Then measure
agreement between the human and the LLM grader using Cohen's kappa. Require
kappa >= 0.80." Everything reported so far is grader-vs-grader agreement, which
does not discharge that requirement -- two automatic graders can agree perfectly
and both be wrong, and judge-1 scoring below chance is proof the risk is real.

This module does the three mechanical parts. The labelling itself is yours.

  1. --sample : draw a stratified random subset and write a BLINDED worksheet.
                The worksheet carries only the captured text. Condition, model,
                wording, and both graders' verdicts are withheld, because a
                labeller who can see them is not an independent rater. The join
                key is an opaque id; the de-blinding key is written to a separate
                file you must not open until labelling is finished.
  2. (human)  : fill the `label` column with one of the 8 pre-registered buckets.
  3. --kappa  : Cohen's kappa, human vs keyword grader and human vs LLM judge,
                REPORTED BY STRATUM. Pooling is what produced the misleading
                0.715 figure earlier: the bare arm has no positives, so one rater
                is constant there and kappa is forced toward 0 regardless of
                agreement (docs/archive/tp_result.md §6).

Usage:
    python label.py --sample runs/<file>.jsonl [--frac 0.2] [--seed 0]
    python label.py --kappa labels/<file>.worksheet.csv --rater human \
        --attestation labels/<file>.attestation.json
    python label.py --selfcheck
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import csv
import glob
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict

from grade import BUCKETS, captured_text, keyword_grade

LABEL_DIR = "labels"


def _rid(row, path):
    """Opaque, stable row id. Includes the file so ids never collide across runs."""
    key = f"{os.path.basename(path)}|{row.get('run_id')}|{row.get('model')}|" \
          f"{row.get('framework')}|{row.get('condition')}|" \
          f"{row.get('wording_style')}|{row.get('rep')}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def sample(path, frac=0.2, seed=0):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if "error" not in r:
                rows.append(r)
    if not rows:
        raise SystemExit(f"no successful rows in {path}")

    # Stratify by (condition, framework) so every cell is represented, then take
    # ceil(frac) from each -- a plain uniform sample can miss small cells entirely.
    strata = defaultdict(list)
    for r in rows:
        strata[(r["condition"], r.get("framework", "raw-api"))].append(r)
    rng = random.Random(seed)
    picked = []
    for key, group in sorted(strata.items()):
        k = max(1, round(len(group) * frac))
        picked.extend(rng.sample(group, min(k, len(group))))
    rng.shuffle(picked)  # so worksheet order leaks no stratum information

    os.makedirs(LABEL_DIR, exist_ok=True)
    base = os.path.basename(path).replace(".jsonl", "")
    work = f"{LABEL_DIR}/{base}.worksheet.csv"
    keyf = f"{LABEL_DIR}/{base}.key.json"
    attestf = f"{LABEL_DIR}/{base}.attestation.json"
    if os.path.exists(work):
        raise SystemExit(f"{work} already exists — refusing to overwrite labels")

    with open(work, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["row_id", "captured_text", "label"])
        for r in picked:
            w.writerow([_rid(r, path), captured_text(r).strip()[:4000], ""])

    key = {}
    for r in picked:
        g = keyword_grade(captured_text(r))
        key[_rid(r, path)] = {
            "condition": r["condition"], "model": r["model"],
            "framework": r.get("framework", "raw-api"),
            "wording_style": r.get("wording_style"),
            "keyword_T1": bool(g["tier_flags"]["T1"]),
            "judge_bucket": r.get("judge_bucket"),
            "source": path,
        }
    with open(keyf, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=1)

    # This is intentionally incomplete. A real human labeler must fill it after
    # labelling; Codex/Claude or another model must not do so on their behalf.
    with open(attestf, "w", encoding="utf-8") as f:
        json.dump({
            "labeler_id": "",
            "labeler_role": "",
            "completed_utc": "",
            "statement": "",
            "required_statement": (
                "I personally assigned every label in this worksheet without "
                "using an AI system to choose or suggest labels."
            ),
        }, f, indent=2)

    print(f"sampled {len(picked)}/{len(rows)} rows ({len(picked)/len(rows):.0%}) "
          f"across {len(strata)} strata")
    print(f"  worksheet (blinded, label this): {work}")
    print(f"  key       (DO NOT OPEN until done): {keyf}")
    print(f"  attestation (human completes):       {attestf}")
    print(f"\nFill the `label` column with exactly one of:\n  " + "\n  ".join(BUCKETS))
    print("\nThen: python label.py --kappa " + work)


def cohens_kappa(a, b):
    """Cohen's kappa for two aligned label sequences."""
    assert len(a) == len(b) and a, "need equal, non-empty sequences"
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(ca) | set(cb))
    if pe == 1.0:
        return float("nan"), po, pe  # both raters constant: kappa undefined
    return (po - pe) / (1 - pe), po, pe


def _validate_human_attestation(path):
    if not path or not os.path.exists(path):
        raise SystemExit("--rater human requires an existing --attestation JSON; "
                         "an AI assistant cannot attest on a person's behalf")
    with open(path, encoding="utf-8") as f:
        a = json.load(f)
    required = a.get("required_statement")
    if not all((a.get("labeler_id"), a.get("labeler_role"),
                a.get("completed_utc"), required)):
        raise SystemExit(f"incomplete human attestation: {path}")
    if a.get("statement") != required:
        raise SystemExit("human attestation statement must exactly equal "
                         "required_statement")


def kappa(worksheet, rater="undeclared", attestation=None):
    keyf = worksheet.replace(".worksheet.csv", ".key.json")
    if not os.path.exists(keyf):
        raise SystemExit(f"missing key file {keyf}")
    with open(keyf, encoding="utf-8") as f:
        key = json.load(f)

    human = {}
    with open(worksheet, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lab = (row.get("label") or "").strip()
            if lab:
                if lab not in BUCKETS:
                    raise SystemExit(f"row {row['row_id']}: {lab!r} is not one of "
                                     f"the 8 pre-registered buckets")
                human[row["row_id"]] = lab
    if not human:
        raise SystemExit("no labels filled in yet — nothing to compare")

    is_human = rater == "human"
    if is_human:
        if len(human) != len(key):
            raise SystemExit(f"human worksheet is incomplete: {len(human)}/{len(key)} "
                             "rows labelled; protocol validation requires all sampled rows")
        _validate_human_attestation(attestation)

    # Human bucket -> binary T1, so it is comparable with the keyword grader.
    t1_buckets = {"framework_identifying", "both_identifying"}
    strata = defaultdict(lambda: {"h": [], "k": [], "j": []})
    for rid, lab in human.items():
        meta = key.get(rid)
        if not meta:
            continue
        stratum = "scaffolded" if meta["framework"] not in ("raw-api", None) else "bare"
        s = strata[stratum]
        s["h"].append(lab in t1_buckets)
        s["k"].append(bool(meta["keyword_T1"]))
        if meta.get("judge_bucket"):
            s["j"].append((lab, meta["judge_bucket"]))

    print(f"labelled {len(human)} of {len(key)} sampled rows")
    print(f"rater = {rater!r}"
          + ("" if is_human else "   <-- NOT a human rater; protocol §5 is NOT discharged"))
    print()
    print(f"{'stratum':14s}{'n':>5}{f'{rater} vs keyword (T1)':>26}{'agree':>9}")
    overall_h, overall_k = [], []
    for name, s in sorted(strata.items()):
        if not s["h"]:
            continue
        k, po, pe = cohens_kappa(s["h"], s["k"])
        overall_h += s["h"]
        overall_k += s["k"]
        kt = "undefined (constant)" if k != k else f"kappa = {k:.3f}"
        print(f"{name:14s}{len(s['h']):>5}{kt:>26}{po:>9.0%}")
    if overall_h:
        k, po, pe = cohens_kappa(overall_h, overall_k)
        kt = "undefined" if k != k else f"kappa = {k:.3f}"
        print(f"{'POOLED':14s}{len(overall_h):>5}{kt:>26}{po:>9.0%}")
        print("\n  Report the STRATIFIED figures. Pooling across an arm where one")
        print("  rater is constant drags a true 1.00 down and is not interpretable.")

    jh = [(a, b) for s in strata.values() for a, b in s["j"]]
    if jh:
        k, po, pe = cohens_kappa([a for a, _ in jh], [b for _, b in jh])
        print(f"\nhuman vs LLM judge (8 buckets), n={len(jh)}: "
              f"kappa = {k:.3f}, raw agreement {po:.0%}")
    else:
        print("\nhuman vs LLM judge: no judged rows in this sample "
              "(run grade.py <file> first to produce judge_bucket)")

    if overall_h:
        k, _, _ = cohens_kappa(overall_h, overall_k)
        bar = 0.80
        if k != k:
            return
        if is_human:
            print(f"\nprotocol §5 requires human kappa >= {bar:.2f}: "
                  f"{'MET' if k >= bar else '*** NOT MET — revise the rubric and re-grade ***'}")
        else:
            print(f"\nprotocol §5 requires a HUMAN rater. This run used rater={rater!r},")
            print("so §5 remains OUTSTANDING regardless of the value above. A high kappa")
            print("between two automatic graders is not evidence that either is correct —")
            print("judge-1 agreed with itself perfectly and scored below chance against")
            print("the keyword grader.")


def _selfcheck():
    a = ["x", "x", "y", "y"]
    k, po, pe = cohens_kappa(a, a)
    assert abs(k - 1.0) < 1e-9 and po == 1.0
    k, _, _ = cohens_kappa(["x", "y", "x", "y"], ["y", "x", "y", "x"])
    assert k < 0, k
    k, _, _ = cohens_kappa(["x", "x"], ["x", "x"])
    assert k != k, "constant raters must give undefined kappa, not 1.0"
    # a known worked example: 2x2 with po=0.8, pe=0.5 -> kappa=0.6
    h = [True] * 4 + [False] * 4 + [True] * 1 + [False] * 1
    m = [True] * 4 + [False] * 4 + [False] * 1 + [True] * 1
    k, po, pe = cohens_kappa(h, m)
    assert abs(po - 0.8) < 1e-9 and abs(k - 0.6) < 1e-9, (k, po, pe)
    print("label selfcheck: PASS")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample")
    ap.add_argument("--kappa")
    ap.add_argument("--frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rater", default="undeclared",
                    help="who produced the labels. Only --rater human can discharge "
                         "protocol §5; anything else is reported as a second grader.")
    ap.add_argument("--attestation",
                    help="human-completed JSON attestation; required with --rater human")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        _selfcheck()
    elif a.sample:
        sample(a.sample, a.frac, a.seed)
    elif a.kappa:
        kappa(a.kappa, a.rater, a.attestation)
    else:
        ap.print_help()
        sys.exit(1)
