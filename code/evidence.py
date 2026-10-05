"""Strict evidence readers and an offline, exhaustive run inventory.

No historical artifact is edited. Inventory warnings expose legacy gaps instead
of retroactively assigning provenance or inventing missing observations.
"""
import _root  # noqa: F401
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import yaml
import providers

SELECTION = Path("data/artifact_selection.json")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    def reject_constant(value):
        raise ValueError(f"non-finite JSON value {value}")

    def unique_object(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON member {key!r}")
            out[key] = value
        return out

    rows = []
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                row = json.loads(line, parse_constant=reject_constant, object_pairs_hook=unique_object)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path}:{number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{number}: expected a JSON object")
            rows.append(row)
    return rows


def trial_key(row):
    return tuple(row.get(k) for k in ("run_id", "provider", "model", "framework",
                                     "condition", "wording_style", "rep", "task_id", "tool_offered"))


def validate_trials(rows, path):
    seen = set()
    for i, row in enumerate(rows, 1):
        if not all(k in row for k in ("model", "condition", "rep", "wording_style")):
            raise ValueError(f"{path}:{i}: missing trial factors")
        if "error" not in row and not isinstance(row.get("tool_called"), bool):
            raise ValueError(f"{path}:{i}: tool_called must be boolean")
        if "error" not in row and row.get("tool_called") and not isinstance(row.get("params_passed"), dict):
            raise ValueError(f"{path}:{i}: missing or malformed emitted arguments")
        key = row.get("trial_id") or trial_key(row)
        if key in seen:
            raise ValueError(f"{path}:{i}: duplicate trial identity")
        seen.add(key)


def selection():
    return json.loads(SELECTION.read_text())["artifacts"]


def selected_paths(candidates):
    """No fallback/ranking: selected evidence must exist and match its digest."""
    # The selection file uses POSIX paths; glob on Windows yields backslashes.
    candidates = {Path(c).as_posix() for c in candidates}
    chosen = []
    for entry in selection():
        if entry["path"] not in candidates:
            continue
        if digest(entry["path"]) != entry["sha256"]:
            raise ValueError(f"selected evidence changed: {entry['path']}")
        chosen.append(entry)
    return chosen


def inventory():
    stages = yaml.safe_load(Path("config.yaml").read_text())["stages"]
    selected = {x["path"]: x for x in selection()}
    output = []
    for path in sorted(Path("runs").glob("*.jsonl")):
        # Inventory derived and raw files too, but never treat them as independent trials.
        kind = "raw" if ".raw." in path.name else "canonical" if path.name.count(".") == 1 else "derived"
        item = {"path": path.as_posix(), "sha256": digest(path), "kind": kind}
        try:
            rows = read_jsonl(path.as_posix())   # POSIX path in recorded messages
        except ValueError as exc:
            item["validation_error"] = str(exc)
            output.append(item)
            continue
        stage = path.name.split("-live-")[0].split("-dry-")[0]
        config = stages.get(stage)
        meta_path = path.with_suffix(".meta.json")
        raw_path = path.with_suffix(".raw.jsonl")
        errors = sum("error" in r for r in rows)
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else None
        identities = Counter()
        if kind == "raw":
            for r in rows:
                requested = r.get("model")
                raw = r.get("raw_provider_response")
                try:
                    status = providers.check_served_model(requested, raw) if requested else "unverified"
                except RuntimeError:
                    status = "mismatch"
                identities[(requested, providers.served_model(raw), status)] += 1
        item.update(stage=stage if config else None, configuration=config,
                    protocol=config.get("preregistration") if config else None,
                    rows=len(rows), errors=errors,
                    temperatures=sorted({r["temperature"] for r in rows if "temperature" in r}),
                    requested_models=sorted({r["model"] for r in rows if r.get("model")}),
                    metadata=meta,
                    raw_path=raw_path.as_posix() if kind == "canonical" and raw_path.exists() else None,
                    selected=selected.get(path.as_posix()),
                    served_identities=[dict(requested=k[0], served=k[1], status=k[2], rows=v)
                                       for k, v in identities.items()])
        if kind == "canonical" and rows and "model" in rows[0]:
            try:
                validate_trials(rows, path.as_posix())
            except ValueError as exc:
                item["validation_error"] = str(exc)
        output.append(item)
    return {"schema_version": 1, "config_sha256": digest("config.yaml"),
            "scope": "All runs/*.jsonl; raw/derived copies are not independent trials",
            "artifacts": output}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = inventory()
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        Path("data/evidence_inventory.json").write_text(text)
        print(f"inventoried {len(result['artifacts'])} artifacts")
    else:
        print(text)


if __name__ == "__main__":
    main()
