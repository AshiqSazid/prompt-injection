"""
run.py — execute a stage and write append-only JSONL (one row per trial).

Usage:
    python run.py --stage gate --dry-run          # offline plumbing test (no keys)
    python run.py --stage gate                     # real gate: 3 models x 5 conds x 30 reps
    python run.py --stage gate --limit 5           # tiny smoke test against real APIs

Each row matches the schema in protocol.md §11. Logs are append-only and never
edited. After a run, analyze with:  python analyze.py runs/<file>.jsonl
"""
import _root  # noqa: F401  -- chdir to the repo root; must come first
                            #  (relative data paths depend on it)
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import time
import traceback
import uuid
import random
from pathlib import Path
import sys
from importlib import metadata as package_metadata

import yaml

import conditions
import providers
import evidence
from grade import keyword_grade, captured_text, load_dotenv


def call_with_retry(*a, retries=6, **kw):
    """Retry on rate-limit (429) with backoff. Free tiers (notably Gemini at
    5 req/min) otherwise fail nearly every trial in a long stage.
    Honours the provider's 'retry in Xs' hint when it gives one.
    ponytail: no tenacity dependency, one loop."""
    for attempt in range(retries):
        try:
            return providers.call(*a, **kw)
        except Exception as e:
            msg = str(e)
            if "429" not in msg and "RESOURCE_EXHAUSTED" not in msg.upper():
                raise
            if attempt == retries - 1:
                raise
            m = re.search(r"retry in ([\d.]+)s", msg)
            time.sleep(min(float(m.group(1)) + 1 if m else 5 * 2 ** attempt, 90))


def load_stage(stage):
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)
    if stage not in cfg["stages"]:
        raise SystemExit(f"stage {stage!r} not in config.yaml")
    return cfg["stages"][stage]


# Which env var each provider needs. Checked BEFORE any spend so a missing key
# stops the run instead of producing one error row per trial (the old behaviour:
# a 300-trial stage would burn through and write 300 identical auth failures).
_PROVIDER_KEYS = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "openai": ("OPENAI_API_KEY",),
    "google": ("GOOGLE_API_KEY", "GEMINI_API_KEY"),  # either satisfies the SDK
    "openrouter": ("OPENROUTER_API_KEY",),
    "glm": ("GLM_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "langchain_openai": ("OPENAI_API_KEY",),
    "langchain_anthropic": ("ANTHROPIC_API_KEY",),
    "mock": (),
}


def preflight(stage_name, stage, dry_run, out_path):
    """Fail loudly before the first API call. Every check here corresponds to a
    failure that has actually cost a run: a missing `temperature` (wording_ablation
    raised KeyError mid-stage), an unknown wording_style, a bad --out that aliases
    the raw sidecar onto the canonical log, or an absent key."""
    problems = []
    prereg = stage.get("preregistration")
    if prereg and not dry_run:
        problems.extend(_preregistration_problems(stage_name, prereg))
    for key in ("models", "conditions", "reps", "temperature"):
        if key not in stage:
            problems.append(f"stage {stage_name!r} is missing required key {key!r}")
    for cond in stage.get("conditions", []):
        if cond not in conditions.CONDITIONS:
            problems.append(f"unknown condition {cond!r} (known: {conditions.CONDITIONS})")
    needed_keys = set()
    for i, m in enumerate(stage.get("models", [])):
        if not m.get("provider") or not m.get("model"):
            problems.append(f"models[{i}] needs both 'provider' and 'model'")
            continue
        if m["provider"] not in _PROVIDER_KEYS:
            problems.append(f"models[{i}]: unknown provider {m['provider']!r}")
        if m.get("wording_style") and m["wording_style"] not in conditions.C_WORDINGS:
            problems.append(f"models[{i}]: unknown wording_style {m['wording_style']!r}")
        if m.get("payload") and m["payload"] not in conditions.PAYLOADS:
            problems.append(f"models[{i}]: unknown payload {m['payload']!r}")
        if m.get("scaffold") and m["scaffold"] not in conditions.SCAFFOLDS:
            problems.append(f"models[{i}]: unknown scaffold {m['scaffold']!r}")
        if m.get("reticence") is not None and m["reticence"] not in conditions.RETICENCE_LADDER:
            problems.append(f"models[{i}]: unknown reticence rung {m['reticence']!r} "
                            f"(known: {sorted(conditions.RETICENCE_LADDER)})")
        if m.get("real_tool") and m["real_tool"] not in conditions.real_tools():
            problems.append(f"models[{i}]: unknown real_tool {m['real_tool']!r} "
                            "— run harvest_real_tools.py")
        if m.get("payload") and m.get("scaffold"):
            problems.append(f"models[{i}]: payload and scaffold are mutually exclusive")
        if m.get("field_position") not in (None, "before", "after"):
            problems.append(f"models[{i}]: field_position must be 'before' or "
                            f"'after' (got {m['field_position']!r})")
        if m.get("field_required") not in (None, True, False):
            problems.append(f"models[{i}]: field_required must be true or false")
        if not dry_run:
            needed_keys.add(m["provider"])
    if not out_path.endswith(".jsonl"):
        problems.append(f"--out must end in .jsonl (got {out_path!r}); otherwise the "
                        "raw sidecar path aliases the canonical log and truncates it")
    if not isinstance(stage.get("reps"), int) or stage.get("reps", 0) <= 0:
        problems.append("reps must be a positive integer")
    if not stage.get("models") or not stage.get("conditions"):
        problems.append("models and conditions must be nonempty")
    for key, default in (("max_attempts", 3), ("max_tokens", 1024)):
        if not isinstance(stage.get(key, default), int) or stage.get(key, default) <= 0:
            problems.append(f"{key} must be a positive integer")
    for provider in sorted(needed_keys):
        names = _PROVIDER_KEYS[provider]
        if names and not any(os.environ.get(n) for n in names):
            problems.append(f"provider {provider!r} needs one of {' / '.join(names)} "
                            "— not found in environment or .env")
    if problems:
        raise SystemExit("preflight FAILED:\n  - " + "\n  - ".join(problems))


def _git(*args):
    """Small, read-only git helper used by the preregistration guard."""
    return subprocess.run(["git", *args], text=True, capture_output=True, check=False)


def _preregistration_problems(stage_name, protocol_path):
    """Refuse a live confirmatory run without auditable commit-order provenance.

    A protocol merely present in the working tree is not a preregistration.  It
    must already be tracked, committed at HEAD, and byte-clean before the first
    provider call.  Stages opt in with ``preregistration: path`` in config.yaml.
    This cannot retroactively validate data that already exist.
    """
    problems = []
    if not os.path.isfile(protocol_path):
        return [f"confirmatory stage {stage_name!r} requires missing {protocol_path!r}"]
    tracked = _git("ls-files", "--error-unmatch", "--", protocol_path)
    if tracked.returncode:
        problems.append(f"{protocol_path} is not tracked by git; commit the protocol "
                        "before any live confirmatory run")
        return problems
    committed = _git("cat-file", "-e", f"HEAD:{protocol_path}")
    if committed.returncode:
        problems.append(f"{protocol_path} is not present in HEAD; commit it before "
                        "any live confirmatory run")
    dirty = _git("diff", "--quiet", "HEAD", "--", protocol_path)
    if dirty.returncode:
        problems.append(f"{protocol_path} differs from HEAD; a confirmatory protocol "
                        "must be committed and clean")
    return problems


def audit_stages():
    """Every stage that has produced a run artifact must still exist in config.yaml.

    Added after a config edit silently deleted payload_generality_openai,
    payload_generality_anthropic, explicit_vs_benign_openai and
    explicit_payloads_openai — three of which had already produced committed data.
    Dry-running the surviving stages cannot detect a deletion, so the check has to
    come from the artifacts, not the config."""
    import glob
    with open("config.yaml") as f:
        stages = set(yaml.safe_load(f)["stages"])
    seen = {}
    for path in glob.glob("runs/*.jsonl"):
        base = os.path.basename(path)
        for tag in ("-live-", "-dry-"):
            if tag in base:
                seen.setdefault(base.split(tag)[0], []).append(base)
                break
    orphans = {k: v for k, v in seen.items() if k not in stages}
    print(f"{len(stages)} stages in config.yaml; "
          f"{len(seen)} distinct stage names among run artifacts")
    if orphans:
        print("\nORPHANED ARTIFACTS — these stages produced data but are GONE from "
              "config.yaml, so those runs are no longer reproducible:")
        for k, v in sorted(orphans.items()):
            print(f"  {k}  ({len(v)} file(s), e.g. {sorted(v)[0]})")
        return 1
    print("OK: every stage that produced an artifact still exists.")
    return 0


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def planned_trials(stage):
    """Deterministic order: shuffle within replicate blocks, preserving pairing."""
    trials = []
    rng = random.Random(stage.get("randomization_seed", 0))
    for rep in range(stage["reps"]):
        block = [(index, m, cond, rep) for index, m in enumerate(stage["models"])
                 for cond in stage["conditions"]]
        rng.shuffle(block)
        trials.extend(block)
    return trials


def trial_spec(m, cond):
    return conditions.build(cond, scaffold=m.get("scaffold"),
                            wording_style=m.get("wording_style", "default"),
                            payload=m.get("payload"), reticence=int(m.get("reticence", 0)),
                            real_tool=m.get("real_tool"),
                            field_required=m.get("field_required", True),
                            field_position=m.get("field_position", "after"))


def atomic_meta(path, value):
    temporary = str(path) + "." + uuid.uuid4().hex + ".tmp"
    with open(temporary, "x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def validate_resume(out_path, meta, fingerprint, trial_ids):
    if meta.get("schema_version") != 2 or meta.get("fingerprint") != fingerprint:
        raise ValueError("resume requires identical version, configuration, code, fixtures and dry-run mode")
    if meta.get("in_flight"):
        raise ValueError("interrupted in-flight request has unknown outcome; reconcile before resuming")
    for path, expected in meta.get("artifact_sha256", {}).items():
        if evidence.digest(path) != expected:
            raise ValueError(f"resume artifact digest mismatch: {path}")
    rows = evidence.read_jsonl(out_path)
    evidence.validate_trials(rows, out_path)
    ids = [r.get("trial_id") for r in rows]
    if any(i not in trial_ids for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("resume found unknown or duplicate trial IDs")
    if any(r.get("run_id") != meta["run_id"] for r in rows):
        raise ValueError("resume found a different run identity")
    raw = evidence.read_jsonl(str(out_path).replace(".jsonl", ".raw.jsonl"))
    raw_ids = [r.get("trial_id") for r in raw]
    expected_raw = {r["trial_id"] for r in rows if "error" not in r or r.get("raw_recorded")}
    if len(raw_ids) != len(set(raw_ids)) or set(raw_ids) != expected_raw:
        raise ValueError("raw/canonical records disagree; reconcile interrupted evidence manually")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--stage", default="gate")
    ap.add_argument("--dry-run", action="store_true", help="mock provider; no network")
    ap.add_argument("--limit", type=int, default=0, help="maximum new trials this invocation")
    ap.add_argument("--out", default=None)
    ap.add_argument("--resume", action="store_true", help="resume a matching version-2 run")
    args = ap.parse_args()
    if args.audit:
        raise SystemExit(audit_stages())
    if args.limit < 0 or (args.resume and not args.out):
        ap.error("--limit must be nonnegative; --resume requires --out")
    load_dotenv()
    stage = load_stage(args.stage)
    preflight(args.stage, stage, args.dry_run, args.out or "runs/x.jsonl")
    trials = planned_trials(stage)
    # Resolve every spec before a provider call; malformed later cells cannot
    # burn a partial budget. Frozen hashes also detect fixture edits on resume.
    specs = [trial_spec(m, cond) for _, m, cond, _ in trials]
    from jsonschema import validators
    for spec in specs:
        schema = spec["tool"]["parameters"]
        validators.validator_for(schema).check_schema(schema)
    code_hashes = {str(p): evidence.digest(p) for p in sorted(Path("code").glob("*.py"))}
    protocol_hash = evidence.digest(stage["preregistration"]) if stage.get("preregistration") else None
    environment = {"python": sys.version,
                   "packages": sorted((d.metadata.get("Name", "unknown"), d.version)
                                      for d in package_metadata.distributions())}
    fingerprint = stable_hash({"stage_name": args.stage, "stage": stage,
                               "specs": specs, "code": code_hashes, "protocol": protocol_hash,
                               "environment": environment, "dry_run": args.dry_run})
    trial_ids = [stable_hash([fingerprint, index, cond, rep])
                 for index, m, cond, rep in trials]
    tag = "dry" if args.dry_run else "live"
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:12]
    out_path = args.out or f"runs/{args.stage}-{tag}-{run_id}.jsonl"
    raw_path = out_path.replace(".jsonl", ".raw.jsonl")
    meta_path = out_path.replace(".jsonl", ".meta.json")
    paths = (out_path, raw_path, meta_path)
    if args.resume:
        if not all(Path(p).is_file() for p in paths):
            raise SystemExit("resume requires canonical, raw, and metadata files")
        meta = json.loads(Path(meta_path).read_text())
        previous = validate_resume(out_path, meta, fingerprint, set(trial_ids))
        run_id = meta["run_id"]
    else:
        if any(Path(p).exists() for p in paths):
            raise SystemExit("output collision: existing evidence will not be appended/overwritten; use --resume")
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        previous = []
        meta = {"schema_version": 2, "run_id": run_id, "stage": args.stage,
                "dry_run": args.dry_run, "fingerprint": fingerprint,
                "configuration": stage, "code_sha256": code_hashes,
                "protocol_sha256": protocol_hash, "environment": environment,
                "expected_trials": len(trials), "planned_trial_ids": trial_ids,
                "canonical_path": out_path, "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    seen = {r["trial_id"] for r in previous}
    done = sum("error" not in r for r in previous)
    errors = len(previous) - done
    pending = [(tid, trial, spec) for tid, trial, spec in zip(trial_ids, trials, specs) if tid not in seen]
    if args.limit:
        pending = pending[:args.limit]
    meta.update(complete=False, status="running", rows_written=len(previous), ok=done, errors=errors)
    atomic_meta(meta_path, meta)
    print(f"[{args.stage}] {len(pending)} remaining/requested trials -> {out_path}")
    mode = "a" if args.resume else "x"
    try:
        with open(out_path, mode, encoding="utf-8") as stream, open(raw_path, mode, encoding="utf-8") as raw:
            for tid, (index, m, cond, rep), spec in pending:
                seed = int(tid[:8], 16)
                schema = spec["tool"]["parameters"]
                row = {"schema_version": 2, "trial_id": tid, "run_id": run_id,
                       "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                       "provider": m["provider"], "model": m["model"],
                       "framework": m.get("framework") or m.get("scaffold") or "raw-api",
                       "condition": cond, "wording_style": m.get("wording_style", "default"),
                       "temperature": stage["temperature"], "seed": seed, "rep": rep,
                       "task_id": m.get("task_id") or ("real-tool:" + m["real_tool"] if m.get("real_tool") else "orders-v1"),
                       "tool_offered": spec["tool"]["name"], "schema_sha256": stable_hash(schema),
                       "spec_sha256": stable_hash(spec), "mock": args.dry_run}
                try:
                    meta["in_flight"] = tid
                    atomic_meta(meta_path, meta)
                    res = call_with_retry(m["provider"], m["model"], spec, stage["temperature"],
                                          dry_run=args.dry_run, seed=seed,
                                          max_tokens=stage.get("max_tokens", 1024),
                                          retries=stage.get("max_attempts", 3))
                    row.update(tool_called=res["tool_called"], params_passed=res["params"],
                               raw_response=res["text"])
                    for key in ("tool_name", "served_model", "identity_status", "arguments_parsed",
                                "schema_valid", "tool_name_matches", "dispatched", "server_received"):
                        row[key] = res.get(key)
                    graded = keyword_grade(captured_text(row))
                    row.update(tier_flags=graded["tier_flags"], keyword_hits=graded["keyword_hits"])
                    raw.write(json.dumps({"trial_id": tid, "run_id": run_id, "model": m["model"],
                                          "provider": m["provider"], "condition": cond, "rep": rep,
                                          "raw_provider_response": res.get("raw")}) + "\n")
                    raw.flush()
                    os.fsync(raw.fileno())
                    row["raw_recorded"] = True
                    done += 1
                except Exception as exc:
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    if isinstance(exc, providers.ModelIdentityError):
                        row.update(identity_status="mismatch", served_model=providers.served_model(exc.raw_response))
                        raw.write(json.dumps({"trial_id": tid, "run_id": run_id,
                                              "model": m["model"], "provider": m["provider"],
                                              "error": row["error"],
                                              "raw_provider_response": exc.raw_response}) + "\n")
                        raw.flush()
                        os.fsync(raw.fileno())
                        row["raw_recorded"] = True
                    errors += 1
                stream.write(json.dumps(row, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                meta.update(rows_written=done + errors, ok=done, errors=errors)
                meta["in_flight"] = None
                meta["artifact_sha256"] = {p: evidence.digest(p) for p in (out_path, raw_path)}
                atomic_meta(meta_path, meta)
                if row.get("identity_status") == "mismatch":
                    raise RuntimeError("model identity mismatch; run halted after preserving raw response")
        meta["status"] = "complete" if done == len(trials) and errors == 0 else "partial"
    except BaseException as exc:
        meta["status"] = "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit)) else "failed"
        raise
    finally:
        meta.update(complete=meta["status"] == "complete",
                    updated_at=dt.datetime.now(dt.timezone.utc).isoformat())
        meta["artifact_sha256"] = {p: evidence.digest(p) for p in (out_path, raw_path) if Path(p).exists()}
        atomic_meta(meta_path, meta)
    print(f"STATUS: {meta['status'].upper()} ({done} ok, {errors} errors; {len(trials)} planned)")


if __name__ == "__main__":
    main()
