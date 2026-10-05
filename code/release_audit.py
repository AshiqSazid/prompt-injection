"""Read-only release checks and optional private clean-tree reproduction.

Never rewrites history or publishes an artifact. Prints paths/counts, not secret
values. Findings require human review; this is not a secret-scanner certificate.
"""
import _root  # noqa: F401
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def export_paths():
    tracked = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    paths = {Path(p) for p in tracked if p}
    for pattern in ('code/*.py', 'data/**/*.json', 'docs/*.md', 'requirements-analysis.*',
                    '.github/workflows/*.yml', 'Q1_READINESS_AUDIT.md',
                    'journal_paper/*.tex', 'journal_paper/*.bib', 'journal_paper/*.md',
                    'journal_paper/*.json'):
        paths.update(Path('.').glob(pattern))
    forbidden = {'.git', '.env', '.venv', '.venv-q1', '.cache', '.firecrawl'}
    unrelated = {'PRT671_Assessment2_Final.docx', 'PRT_671____Interim_Report.pdf', 'abir.pdf'}
    return sorted(p for p in paths if p.is_file() and not p.is_symlink()
                  and p.name not in unrelated
                  and not any(part in forbidden for part in p.parts))


def inspect(paths):
    findings = []
    for path in paths:
        if path.suffix not in ('.py', '.md', '.tex', '.json', '.jsonl', '.yaml', '.yml', '.bib'):
            continue
        text = path.read_text(errors='replace')
        categories = []
        if re.search(r'/home/[^/\s]+|/Users/[^/\s]+|moodifai|Rafiur Rahman', text, re.I):
            categories.append('author_or_local_path_identifier')
        if re.search(r'github\.com/(?!modelcontextprotocol|open-telemetry|InvariantLabs)[^/\s]+/schema-disclosure-gap', text, re.I):
            categories.append('identifying_repository_link')
        if re.search(r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}', text):
            categories.append('possible_api_key_requires_review')
        if categories:
            findings.append({'path': str(path), 'categories': categories})
    history_authors = subprocess.check_output(['git', 'log', '--format=%an <%ae>']).decode().splitlines()
    return {'status': 'review_required', 'files_in_private_export': len(paths), 'findings': findings,
            'distinct_history_author_identities': len(set(history_authors)),
            'history_policy': 'Do not ship .git for anonymous review; history was not rewritten.',
            'excluded': ['.git', '.env', '.cache', '.firecrawl', '.venv', '.venv-q1', 'identified unrelated root PDFs/DOCX, even when tracked'],
            'remaining_checks': ['PDF metadata and visual author marks', 'license permissions', 'all identifying links',
                                 'independent secret scan', 'venue anonymity policy']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--clean-check', action='store_true')
    args = parser.parse_args()
    paths = export_paths()
    result = inspect(paths)
    if args.write:
        Path('data/release_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    else:
        print(json.dumps(result, indent=2))
    if args.clean_check:
        with tempfile.TemporaryDirectory(prefix='schema-private-repro-') as temporary:
            target = Path(temporary)
            for path in paths:
                destination = target / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
            for extra in ('data/release_audit.json',):
                if Path(extra).exists(): shutil.copy2(extra, target / extra)
            subprocess.run([sys.executable, 'code/reproduce.py'], cwd=target, check=True)
            subprocess.run([sys.executable, 'code/reproduce.py', '--papers-only'], cwd=target, check=True)
            print('Private clean-tree reproduction passed without .env, .git, or caches; no public export made.')


if __name__ == '__main__':
    main()
