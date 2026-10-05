"""Fail-closed author/venue gate, distinct from numerical reproducibility.

Records are attestations for human review, not an automated quality or Q1
certificate. A complete record must include a decision, reviewer and evidence.
No email, upload, inference, publication or submission is performed.
"""
import _root  # noqa: F401
import argparse
import json
from pathlib import Path

import evidence


REQUIRED = ('venue_scope_and_sjr', 'authors_and_approval', 'funding_and_conflicts',
            'prior_publication', 'disclosure_decision', 'release_and_licenses',
            'literature_and_novelty', 'statistical_review', 'evidence_scope_decision',
            'timestamp_provenance', 'ai_use_declaration', 'venue_format_and_files')
MANUSCRIPTS = ('journal_paper/main.tex', 'journal_paper/supplement.tex')


def inspect(record):
    issues = []
    if record.get('schema_version') != 1:
        issues.append('unsupported or missing decision-record version')
    decisions = record.get('decisions', {})
    for key in REQUIRED:
        value = decisions.get(key, {}) if isinstance(decisions, dict) else {}
        if not isinstance(value, dict) or value.get('status') != 'confirmed':
            issues.append(f'{key}: author/reviewer confirmation pending')
            continue
        for field in ('decision', 'reviewer', 'evidence', 'reviewed_on'):
            if not isinstance(value.get(field), str) or not value[field].strip():
                issues.append(f'{key}: missing {field}')
    hashes = record.get('approved_manuscript_sha256', {})
    for path in MANUSCRIPTS:
        if not isinstance(hashes, dict) or hashes.get(path) != evidence.digest(path):
            issues.append(f'{path}: final author approval absent or stale')
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--record', default='data/submission_decisions.json')
    args = parser.parse_args()
    record = json.loads(Path(args.record).read_text())
    issues = inspect(record)
    print(json.dumps({'status': 'not_submission_ready' if issues else 'documented_gates_complete',
                      'issues': issues,
                      'limitation': 'Administrative evidence only; not editorial acceptance, quartile verification by software, or authorization to submit.'}, indent=2))
    raise SystemExit(1 if issues else 0)


if __name__ == '__main__':
    main()
