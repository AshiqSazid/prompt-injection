"""Build the expanded Elsevier manuscript's assets from the audited analyses.

Reuse the focused manuscript's evidence calculations, not its cached tables.
Only presentation is adapted for full-width floats in a two-column article.
No historical observations, protocols, or focused-manuscript files are changed.
"""
import _root  # noqa: F401
import argparse
import csv
import json
from pathlib import Path
import re

import journal_assets
import label
import paper_details


FOLDER = Path('paper')
TABLES = ('primary_table', 'field_table', 'accounting_table', 'fixture_table',
          'secondary_table', 'sensitivity_table', 'exp25_table', 'exp25_capacity_table')


# Repository labels in the shared journal tables, and the names this manuscript uses.
READER_NAMES = (
    ('Experiment 25 primary endpoint', 'Study~2 primary endpoint'),
    ('(stage A: replicate-block bootstrap. Stage B: schemas within tasks)',
     '(Study~2a: replicate-block bootstrap. Study~2b: schemas within tasks)'),
    ('Stage & Model', 'Study & Model'),
    ('A (two synthetic tools)', '2a (two synthetic tools)'),
    ('B (eight native schemas)', '2b (eight native schemas)'),
    ('Experiment 25 capacity arm (stage A, orders tool)', 'Study~2a capacity arm (orders tool)'),
    ('Selected v3 artifact accounting', 'Study~1 run accounting'),
    ('protocol-named', 'preregistered'),
)


FIRST_PASS_SHA256 = 'a85486b7f64b6dd339bccebde00c507c65f45f73ebb5fe644cea2210f9a6dde7'


def annotation_macros():
    """Compute worksheet agreement, without asserting human provenance.

    The historical attestation has suffixed multi-author keys incompatible with
    label.py's single-rater validator. Do not repair or attest on the authors'
    behalf; the manuscript explicitly reports that limitation.
    """
    key = json.loads(Path('labels/v4-apidoc-gate.key.json').read_text())
    with Path('labels/v4-apidoc-gate.worksheet.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    ratings = {row['row_id']: row['label'].strip() for row in rows}
    if len(ratings) != len(rows) or set(ratings) != set(key):
        raise ValueError('Human worksheet must contain each sampled row exactly once')
    if not all(value in label.BUCKETS for value in ratings.values()):
        raise ValueError('Invalid or missing historical human label')
    scaffolded = [rid for rid in ratings if key[rid]['framework'] not in ('raw-api', None)]
    binary = {'framework_identifying', 'both_identifying'}
    agreement = label.cohens_kappa(
        [ratings[rid] in binary for rid in scaffolded],
        [bool(key[rid]['keyword_T1']) for rid in scaffolded])[0]
    judged = [rid for rid in ratings if key[rid].get('judge_bucket')]
    judge_agreement = label.cohens_kappa(
        [ratings[rid] for rid in judged], [key[rid]['judge_bucket'] for rid in judged])[0]
    bare = [rid for rid in ratings if rid not in scaffolded]
    def agree(rids):
        return sum((ratings[r] in binary) == bool(key[r]['keyword_T1']) for r in rids)
    values = {'PaperAnnotationRows': str(len(ratings)),
              'PaperAnnotationScaffoldedKappa': f'{agreement:.3f}',
              'PaperAnnotationJudgeKappa': f'{judge_agreement:.3f}',
              'PaperAnnotationScaffoldedAgreeFrac': f'{agree(scaffolded)}/{len(scaffolded)}',
              'PaperAnnotationBareAgreeFrac': f'{agree(bare)}/{len(bare)}',
              'PaperAnnotationJudgeAgreeFrac':
                  f'{sum(ratings[r] == key[r]["judge_bucket"] for r in judged)}/{len(judged)}'}
    # The discarded first pass over the same sample, released as a record, never data.
    import hashlib
    from collections import Counter
    first = Path('labels/v4-apidoc-gate.first-pass-failed.worksheet.csv')
    if hashlib.sha256(first.read_bytes()).hexdigest() != FIRST_PASS_SHA256:
        raise ValueError(f'Discarded labelling record changed: {first}')
    with first.open(newline='') as stream:
        discarded = {row['row_id']: row['label'].strip() for row in csv.DictReader(stream)}
    if set(discarded) != set(key):
        raise ValueError('Discarded worksheet must cover the same sampled rows')
    def first_kappa(rids):
        return label.cohens_kappa([discarded[r] in binary for r in rids],
                                  [bool(key[r]['keyword_T1']) for r in rids])[0]
    values.update({
        'PaperFirstPassModalFrac': f'{Counter(discarded.values()).most_common(1)[0][1]}/{len(discarded)}',
        'PaperFirstPassAgreeFrac': f'{sum((discarded[r] in binary) == bool(key[r]["keyword_T1"]) for r in discarded)}/{len(discarded)}',
        'PaperFirstPassKappa': f'{first_kappa(list(discarded)):.3f}',
        'PaperFirstPassScaffoldedKappa': f'{first_kappa(scaffolded):.3f}'})
    return ''.join(f'\\newcommand{{\\{key}}}{{{value}}}\n' for key, value in values.items())


def wide_tables(source, stem):
    """Convert bounded generated longtables to full-width journal floats."""
    source = re.sub(r'\\endfirsthead.*?\\endhead\n', '', source, flags=re.S)
    blocks = re.findall(
        r'\\begin\{center\}(\\(?:small|scriptsize))\\begin\{longtable\}'
        r'(.*?)\\end\{longtable\}\\end\{center\}', source, re.S)
    if not blocks:
        raise ValueError(f'No generated longtable found for {stem}')
    result = []
    for index, (size, body) in enumerate(blocks, 1):
        caption = re.search(r'\\caption\{([^\n]*)\}\\\\\n', body)
        if caption is None:
            raise ValueError(f'Missing caption in {stem}')
        spec = body[:caption.start()].strip()
        rows = body[caption.end():]
        result.append(
            '\\begin{table*}[t]\\centering' + size + '\n'
            + '\\caption{' + caption[1] + '}\n'
            + f'\\label{{tab:{stem}-{index}}}\n'
            + '\\begin{tabular}' + spec + '\n' + rows
            + '\\end{tabular}\n\\end{table*}\n')
    return '\n'.join(result)


def outputs():
    audited = journal_assets.outputs()
    out = {'analysis_numbers.tex': audited['journal_numbers.tex'] + annotation_macros()}
    for stem in TABLES:
        source = audited[stem + '.tex']
        source = re.sub(r';\s*([a-z])', lambda m: '. ' + m[1].upper(), source).replace(';', '.')
        if r'\begin{longtable}' in source:
            source = wide_tables(source, stem)
        if stem == 'exp25_table':   # five columns overflow one elsarticle column
            source = source.replace(r'\begin{table}', r'\begin{table*}').replace(r'\end{table}', r'\end{table*}')
        source = source.replace('The supplement gives full descriptions and marker aliases.',
                                'Full descriptions and marker aliases appear in \\ref{app:fixtures}.')
        for label, name in READER_NAMES:   # paper-only: journal_paper/ keeps the artifact labels
            source = source.replace(label, name)
        out['generated_' + stem + '.tex'] = '% Generated by code/paper_assets.py; do not edit.\n' + source
    entries = journal_assets.bib_entries((FOLDER / 'refs.bib').read_text())
    entries.update(journal_assets.bib_entries(Path('journal_paper/additional_refs.bib').read_text()))
    # Verified corrections for this manuscript only. The two sources above also
    # feed journal_paper/, whose generated bibliography is hash-locked.
    if (FOLDER / 'refs_overrides.bib').exists():
        entries.update(journal_assets.bib_entries((FOLDER / 'refs_overrides.bib').read_text()))
    # elsarticle-num prints the eprint itself, so an arXiv id in howpublished prints twice.
    entries = {k: re.sub(r'(howpublished\s*=\s*\{arXiv preprint) arXiv:[^}]*\}', r'\1}', v)
                  if re.search(r'\beprint\s*=', v) else v for k, v in entries.items()}
    manuscript = (FOLDER / 'main.tex').read_text()
    keys = sorted({key for match in re.finditer(r'\\cite\w*\{([^}]+)\}', manuscript)
                   for key in match[1].split(',')})
    missing = set(keys) - entries.keys()
    if missing:
        raise ValueError(f'Missing references: {missing}')
    out['journal_refs.bib'] = (
        '% Generated from paper/refs.bib and journal_paper/additional_refs.bib.\n'
        '% Edit those source records, not this generated bibliography.\n\n'
        + '\n\n'.join(entries[key] for key in keys) + '\n')
    out.update(paper_details.outputs())
    return out


def typed_numbers(tex):
    """Result numbers typed into the manuscript body instead of taken from macros."""
    body = tex.split(r'\begin{document}', 1)[1]
    body = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', '', body, flags=re.S)
    body = re.sub(r'(?<!\\)%.*', '', body)
    return re.findall(r'\b\d+/\d+\b|\[\d+(?:\.\d+)?, ?\d+(?:\.\d+)?\]|\d+\.\d+\\%', body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, content in outputs().items():
        path = FOLDER / name
        if args.write:
            path.write_text(content)
        elif not path.exists() or path.read_text() != content:
            stale.append(str(path))
    if stale:
        raise ValueError('Stale expanded-manuscript assets: ' + ', '.join(stale))
    typed = typed_numbers((FOLDER / 'main.tex').read_text())
    if args.check and typed:
        raise ValueError('Typed numbers in paper/main.tex, use generated macros: ' + ', '.join(typed))
    print('Expanded journal tables, analysis macros and bibliography '
          + ('regenerated.' if args.write else 'verified against source evidence.'))


if __name__ == '__main__':
    main()
