"""Check the research artifact without credentials, SDK calls or cache downloads.

--papers-only compiles copies in temporary directories, preserving source PDFs.
"""
import _root  # noqa: F401
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def command(args, cwd=None):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, cwd=cwd, check=True)


def papers(write=False):
    for folder, document in (('paper', 'main'), ('usenix_paper', 'main'),
                             ('journal_paper', 'main'), ('journal_paper', 'supplement')):
        with tempfile.TemporaryDirectory(prefix='schema-paper-') as temporary:
            dest = Path(temporary) / folder
            shutil.copytree(folder, dest, ignore=shutil.ignore_patterns('main.pdf', 'supplement.pdf', '*.aux', '*.log', '*.out', '*.bbl', '*.blg'))
            passes = [['pdflatex', '-interaction=nonstopmode', '-halt-on-error', document + '.tex']]
            if document != 'supplement':
                passes.append(['bibtex', document])
            passes.extend([['pdflatex', '-interaction=nonstopmode', '-halt-on-error', document + '.tex']] * 2)
            for args in passes:
                result = subprocess.run(args, cwd=dest, text=True, capture_output=True)
                if result.returncode:
                    print(result.stdout[-8000:])
                    print(result.stderr[-2000:])
                    raise RuntimeError(f'{folder}: failed {args[0]}')
            log = (dest / (document + '.log')).read_text()
            if 'There were undefined references' in log or 'There were undefined citations' in log:
                raise RuntimeError(f'{folder}: unresolved citations/references')
            print(f'{folder}/{document}: clean {len(passes)}-pass build passed')
            if write:
                shutil.copy2(dest / (document + '.pdf'), Path(folder) / (document + '.pdf'))
                print(f'updated {folder}/{document}.pdf')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--papers-only', action='store_true')
    parser.add_argument('--write-papers', action='store_true', help='publish locally built PDFs into the two manuscript folders')
    args = parser.parse_args()
    if args.papers_only or args.write_papers:
        papers(write=args.write_papers)
        return
    command([sys.executable, '-m', 'unittest', 'discover', '-s', 'code', '-p', 'test*.py'])
    command([sys.executable, 'code/manifest.py', '--check'])
    tables = subprocess.run([sys.executable, 'code/make_tables.py', '--check'], text=True, capture_output=True)
    if tables.returncode:
        print(tables.stdout, tables.stderr)
        raise RuntimeError('artifact-backed table regeneration failed')
    print(f'Tables regenerated and checked ({len(tables.stdout.splitlines())} lines).')
    import make_v3_report
    if Path('updated_v6_result.md').read_text() != make_v3_report.build():
        raise RuntimeError('generated v3 report is stale')
    import evidence
    def scientific_inventory(value):
        # The exhaustive local audit includes ignored mock files. A clean checkout
        # must reproduce scientific inputs, not require publishing mock outputs.
        return {**value, 'artifacts': [a for a in value['artifacts'] if '-dry-' not in a['path']]}
    if scientific_inventory(evidence.inventory()) != scientific_inventory(json.loads(Path('data/evidence_inventory.json').read_text())):
        raise RuntimeError('evidence inventory is stale or the historical archive changed')
    import q1_analysis
    result = json.loads(json.dumps(q1_analysis.build(), allow_nan=False))
    saved = json.loads(Path('data/q1_analysis.json').read_text())
    for key in ('primary_crosscheck', 'per_fact', 'temperature_zero', 'primary_decision'):
        if result[key] != saved[key]:
            raise RuntimeError(f'statistical appendix drift: {key}')
    if not result['hierarchical']['converged']:
        raise RuntimeError('hierarchical secondary fit failed to converge')
    import journal_assets
    journal_assets.check_or_write()
    import extension_harness
    extension_harness.check_or_write()
    print('Offline extension engineering fixtures verified; not new model evidence.')
    print('Focused journal manuscript tables and bibliography verified fresh.')
    print('Offline reproduction passed; no new scientific observations or API calls.')


if __name__ == '__main__':
    main()
