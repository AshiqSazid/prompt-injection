"""Generate the focused journal manuscript's tables from declared raw evidence.

No providers, downloads or cached manuscript values are used. --check detects
stale tables, numbers and bibliography; --write is an explicit regeneration.
"""
import _root  # noqa: F401
import argparse
import hashlib
import json
from pathlib import Path
import re

import conditions
import evidence
import make_v3_report as v3
import manifest
import q1_analysis
import scoring_sensitivity


FOLDER = Path('journal_paper')
NAMES = {'gpt-4o': 'GPT-4o', 'gemini-3-flash-preview': 'Gemini Flash',
         'claude-sonnet-4-5-20250929': 'Claude Sonnet', 'deepseek-v4-flash': 'DeepSeek Flash',
         'gemini-3.1-pro-preview': 'Gemini Pro'}


def esc(text):
    return str(text).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')


def frac(pair):
    return f'{pair[0]}/{pair[1]}'


def interval(values, digits=1):
    return '[' + ', '.join(f'{100 * v:.{digits}f}' for v in values) + ']'


def bib_entries(text):
    """Extract whole balanced BibTeX entries, excluding inter-entry comments."""
    entries = {}
    for match in re.finditer(r'^@\w+\{([^,]+),', text, re.M):
        key = match[1]
        if key in entries:
            raise ValueError(f'duplicate bibliography key: {key}')
        depth = 1
        for end in range(match.end(), len(text)):
            if text[end] == '{' and text[end - 1] != '\\': depth += 1
            if text[end] == '}' and text[end - 1] != '\\': depth -= 1
            if depth == 0:
                entries[key] = text[match.start():end + 1]
                break
        else:
            raise ValueError(f'unclosed bibliography entry: {key}')
    return entries


# Experiment 25 canonical files, declared with their digests (no ranking or
# fallback, as for the v3 selection). Each is one complete provider leg.
EXP25_FILES = {
    ('A', 'gemini-3-flash-preview'): (
        'extension_runs/schema_types-A-live-gemini-3-flash-preview-20260929-173652-035844.jsonl',
        'da0bd934c5398113b95f1c16542479c59536b9945533304948b73dc28ee6985c'),
    ('A', 'gpt-4o-2024-08-06'): (
        'extension_runs/schema_types-A-live-gpt-4o-2024-08-06-20260929-182831-412562.jsonl',
        '8792a9f6354e16eceb9f35e17edff836211b9e13ff35ec82757f3589b5af7510'),
    ('B', 'gemini-3-flash-preview'): (
        'extension_runs/schema_types-B-live-gemini-3-flash-preview-20260929-191521-515596.jsonl',
        '5d7c6cc823521e5a66da0174aaa73b1f7725284b9002c010b31912c4e052b070'),
    ('B', 'gpt-4o-2024-08-06'): (
        'extension_runs/schema_types-B-live-gpt-4o-2024-08-06-20260929-192012-654397.jsonl',
        '9d4e4d8067ff08a0657cca1f2b1a74d8f1e4253e9536cf83f3c09d9b0b0f2659'),
}
EXP25_PREFIX = {'gemini-3-flash-preview': 'Gem', 'gpt-4o-2024-08-06': 'Gpt'}
EXP25_NAMES = {'gemini-3-flash-preview': 'Gemini Flash', 'gpt-4o-2024-08-06': 'GPT-4o'}


def pp(value):
    """A fraction as percentage points with one decimal, never '-0.0'."""
    text = f'{100 * value:.1f}'
    return '0.0' if text == '-0.0' else text


def exp25():
    """Experiment 25 macros and tables, from the declared canonical files through
    the pre-registered schema_types_analyze.summarise(); nothing is re-derived."""
    import schema_types_analyze as analyze
    rows = {}
    for (stage, model), (path, sha) in EXP25_FILES.items():
        if evidence.digest(path) != sha:
            raise ValueError(f'Experiment 25 evidence changed: {path}')
        leg = analyze.load_rows(path)
        if {r['model'] for r in leg} != {model} or {r['stage'] for r in leg} != {stage}:
            raise ValueError(f'unexpected stage or model in {path}')
        rows.setdefault(stage, []).extend(leg)
    macros, summaries, cost = {}, {}, 0.0
    for stage, stage_rows in rows.items():
        s = analyze.summarise(stage_rows)
        if s['collection_status'] != 'complete' or s['mock']:
            raise ValueError(f'Experiment 25 stage {stage} is not a complete live collection')
        summaries[stage] = s
        macros[f'Exp{stage}Trials'] = f'{len(stage_rows):,}'
        stage_cost = sum((r.get('billed_usage') or {}).get('usd', 0) for r in stage_rows)
        cost += stage_cost
        macros[f'Exp{stage}Cost'] = f'{stage_cost:.2f}'
        misses = [r for r in stage_rows if r['arm'] in ('free', 'constrained')
                  and not analyze.target_received(r)]
        first_word = [r for r in misses if r['status'] == 'received'
                      and r['canaries'][r['target_family']].split()[0] in json.dumps(r.get('attack_value'))]
        macros[f'Exp{stage}Misses'] = str(len(misses))
        macros[f'Exp{stage}FirstWord'] = str(len(first_word))
        for model, prefix in EXP25_PREFIX.items():
            p = s['providers'][model]
            c = p['free_vs_constrained']
            n = c['matched_pairs']
            key = f'Exp{stage}{prefix}'
            macros[key + 'Free'] = frac((round(c['free_diagonal_rate'] * n), n))
            macros[key + 'Constrained'] = frac((round(c['constrained_diagonal_rate'] * n), n))
            macros[key + 'Delta'] = pp(c['free_minus_constrained'])
            macros[key + 'DeltaCI'] = '[' + ', '.join(pp(v) for v in c['ci95']) + ']'
            macros[key + 'Rejected'] = frac(c['constrained_schema_rejections'])
            macros[key + 'SelDiag'] = pp(p['selectivity']['diagonal_rate']) + r'\%'
            macros[key + 'SelOff'] = pp(p['selectivity']['off_diagonal_rate']) + r'\%'
            macros[key + 'WrongTool'] = str(sum(r['status'] == 'wrong_tool' for r in stage_rows
                                                if r['model'] == model and r['arm'] in ('free', 'constrained')))
            if stage == 'A':
                macros[key + 'Unplanted'] = frac((p['unplanted']['any_canary_received'], p['unplanted']['trials']))
                for domain, d in p['capacity'].items():
                    name = key + domain.capitalize()
                    macros[name + 'Planted'] = frac(d['planted_correct'])
                    macros[name + 'Unplanted'] = frac(d['unplanted_correct'])
    capacity = [d for m in EXP25_PREFIX for d in summaries['A']['providers'][m]['capacity'].values()]
    macros['ExpAHolmMax'] = f"{max(d['permutation_p_holm'] for d in capacity):.4f}"
    macros['ExpACapacityPlanted'] = frac((sum(d['planted_correct'][0] for d in capacity),
                                          sum(d['planted_correct'][1] for d in capacity)))
    macros['ExpCost'] = f'{cost:.2f}'

    table_rows = []
    for stage, context in (('A', 'two synthetic tools'), ('B', 'eight native schemas')):
        for model, prefix in EXP25_PREFIX.items():
            key = f'Exp{stage}{prefix}'
            table_rows.append(f"{stage} ({context}) & {EXP25_NAMES[model]} & {macros[key + 'Free']} & "
                              f"{macros[key + 'Constrained']} & {macros[key + 'Delta']} {macros[key + 'DeltaCI']}" + r' \\')
    constraint_table = '\n'.join([
        r'\begin{table}[t]\centering\small',
        r'\caption{Experiment 25 primary endpoint: received target recovery with a free '
        r'string versus a canary-permitting pattern/length constraint, exact pairs. '
        r'Difference and 95\% interval in percentage points (stage A: replicate-block '
        r'bootstrap; stage B: schemas within tasks).}',
        r'\label{tab:exp25}', r'\begin{tabular}{@{}llrrr@{}}\toprule',
        r'Stage & Model & Free & Constr. & Diff. [CI] \\\midrule', *table_rows,
        r'\bottomrule\end{tabular}\end{table}', ''])
    capacity_rows = []
    for domain, label, chance in (('enum', 'Enum (8)', '12.5'), ('integer', 'Integer 0--7', '12.5'),
                                  ('boolean', 'Boolean', '50')):
        cells = ' & '.join(f"{macros[f'ExpA{p}{domain.capitalize()}Planted']} & "
                           f"{macros[f'ExpA{p}{domain.capitalize()}Unplanted']}" for p in EXP25_PREFIX.values())
        capacity_rows.append(f'{label} & {chance}\\% & {cells}' + r' \\')
    capacity_table = '\n'.join([
        r'\begin{table}[t]\centering\small',
        r'\caption{Experiment 25 capacity arm (stage A, orders tool): planted admissible '
        r'value received versus a hidden balanced label with nothing planted. Permutation '
        r'tests, Holm-adjusted over all six, $p\le\ExpAHolmMax$.}',
        r'\label{tab:exp25capacity}', r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
        r' & & \multicolumn{2}{c}{Gemini Flash} & \multicolumn{2}{c}{GPT-4o} \\',
        r'Field & Chance & Planted & None & Planted & None \\\midrule', *capacity_rows,
        r'\bottomrule\end{tabular}\end{table}', ''])
    return macros, {'exp25_table.tex': constraint_table, 'exp25_capacity_table.tex': capacity_table}


def outputs():
    matrices = v3.pick(v3.canonical('runs/v3_matrix_*-live-*.jsonl'), v3.matrix_stats)
    unplanted = v3.pick(v3.canonical('runs/v3_unplanted_*-live-*.jsonl'), v3.unplanted_stats)
    primary = {d['model']: d for d in matrices if d['evidence_status'] == 'protocol_named'}
    analysis = q1_analysis.build()
    if analysis['primary_decision'] != 'supported':
        raise ValueError('journal narrative requires revision: primary decision is not supported')
    checks = {d['model']: d for d in analysis['primary_crosscheck']}
    macros = {}
    for model, prefix in [('gpt-4o', 'Gpt'), ('gemini-3-flash-preview', 'Gemini')]:
        macros[f'Journal{prefix}Loo'] = '--'.join(f'{100*x:.1f}' for x in checks[model]['loo_difference'])
    t = analysis['temperature_zero']['counts']
    macros.update(JournalTzeroDiagonal=frac((t['diagonal_k'], t['diagonal_n'])),
                  JournalTzeroOff=frac((t['off_k'], t['off_n'])),
                  JournalTzeroNeutral=frac((t['neutral_any'], t['neutral_calls'])),
                  JournalMixedStatus='converged' if analysis['hierarchical']['converged'] else 'failed')
    exp25_macros, exp25_tables = exp25()
    macros.update(exp25_macros)
    out = {'numbers.tex': manifest.tex_content(manifest.build()),
           'journal_numbers.tex': '% Generated from raw evidence; do not edit.\n' + '\n'.join(
               rf'\newcommand{{\{key}}}{{{value}}}' for key, value in sorted(macros.items())) + '\n'}
    primary_rows = []
    for model in ('gpt-4o', 'gemini-3-flash-preview'):
        d = primary[model]
        delta = d['cluster']['difference']
        primary_rows.append(f"{NAMES[model]} & {frac(d['diag'])} & {frac(d['off'])} & "
                            f"{100*delta[0]:.0f} {interval(delta[1:], 0)}" + r' \\')
    out['primary_table.tex'] = '\n'.join([
        r'\begin{table}[t]\centering\small',
        r'\caption{Primary recovery. M: matched fact checks; U: nonmatched fact checks. '
        r'Difference and paired 95\% interval are percentage points; seven fields per model.}',
        r'\label{tab:primary}', r'\begin{tabular}{@{}lrrr@{}}\toprule',
        r'Model & M & U & Difference [CI] \\\midrule', *primary_rows,
        r'\bottomrule\end{tabular}\end{table}', ''])
    field_rows = []
    for field in conditions.V3_FIELD_TARGET:
        field_rows.append(f"{esc(conditions.C_WORDINGS[field][0])} & {esc(conditions.FIELD_EXPLICITNESS[field])} & " +
                          ' & '.join(frac(primary[m]['per_field'][field]) for m in
                                     ('gpt-4o', 'gemini-3-flash-preview')) + r' \\')
    out['field_table.tex'] = '\n'.join([
        r'\begin{table}[t]\centering\scriptsize',
        r'\caption{Matched recovery by actual field name and prespecified class. '
        r'The supplement gives full descriptions and marker aliases.}',
        r'\label{tab:fields}', r'\begin{tabular}{@{}llrr@{}}\toprule',
        r'Field & Class & GPT-4o & Gemini \\\midrule', *field_rows,
        r'\bottomrule\end{tabular}\end{table}', ''])
    fixture_rows = []
    for field in list(conditions.V3_FIELD_TARGET) + conditions.V3_GENERIC_FIELDS:
        name, description = conditions.C_WORDINGS[field]
        target = conditions.V3_FIELD_TARGET.get(field, 'none')
        fixture_rows.append(f"{esc(name)} & {target} & {esc(description)}" + r' \\')
    fixture_rows.append(r'request\_trace\_id & none & An opaque unique identifier for this request. \\')
    out['fixture_table.tex'] = '\n'.join([
        r'\begin{center}\small\begin{longtable}{@{}p{.30\textwidth}lp{.48\textwidth}@{}}',
        r'\caption{Tested added fields. All are required strings in the primary matrix.}\\',
        r'\toprule Field & Target & Description \\\midrule',
        *fixture_rows, r'\bottomrule\end{longtable}\end{center}',
        r'\begin{center}\small\begin{longtable}{@{}lp{.38\textwidth}p{.38\textwidth}@{}}',
        r'\caption{Synthetic full markers and prespecified aliases, before normalization.}\\',
        r'\toprule Family & Full marker & Aliases \\\midrule',
        *[f"{fact} & {esc(marker)} & {esc(', '.join(aliases))}" + r' \\'
          for fact, (marker, aliases) in conditions.v3_facts().items()],
        r'\bottomrule\end{longtable}\end{center}', ''])
    account = []
    for kind, entries in [('matrix', matrices), ('unplanted', unplanted)]:
        for d in entries:
            called = sum(r['tool_called'] for r in v3.rows_of(d['path']))
            status = 'protocol-named' if d['evidence_status'] == 'protocol_named' else 'post-hoc'
            if kind == 'matrix' and not d['complete']: status += ', incomplete'
            if kind == 'unplanted' and not d['protocol_grid_complete']: status += ', partial fields'
            outcome = frac(d['ctrl_calls']) if kind == 'matrix' else frac((d['canary'], d['called']))
            account.append(f"{NAMES[d['model']]} & {kind} & {d['attempted_rows']} & {d['errors']} & "
                           f"{d['rows']} & {called} & {outcome} & {status}" + r' \\')
    out['accounting_table.tex'] = '\n'.join([
        r'\begin{center}\scriptsize\begin{longtable}{@{}llrrrrlp{.22\textwidth}@{}}',
        r'\caption{Selected v3 artifact accounting. Last outcome is neutral any-canary '
        r'recovery for matrix arms; any-canary recovery for unplanted arms.}\\',
        r'\toprule Model & Arm & Attempts & Errors & Usable & Emitted & Outcome & Status \\\midrule',
        *account, r'\bottomrule\end{longtable}\end{center}', ''])
    secondary = []
    for d in analysis['per_fact']:
        secondary.append(f"{NAMES[d['model']]} & {d['stratum']} & {d['fact']} & "
                         f"{frac(d['diagonal'])} & {frac(d['offdiag'])} & "
                         f"{interval(d['wilson'][1:])} & {interval(d['difference_newcombe'][1:])} & "
                         f"{d['p_holm']:.3g}" + r' \\')
    out['secondary_table.tex'] = '\n'.join([
        r'\begin{center}\scriptsize\begin{longtable}{@{}lllrrlll@{}}',
        r'\caption{Secondary per-fact analyses. Wilson endpoints are percentages; '
        r'Newcombe endpoints are percentage points.}\\',
        r'\toprule Model & Stratum & Fact & M & U & Wilson & Newcombe & Holm $p$ \\\midrule',
        r'\endfirsthead\toprule Model & Stratum & Fact & M & U & Wilson & Newcombe & Holm $p$ \\\midrule\endhead',
        *secondary, r'\bottomrule\end{longtable}\end{center}', ''])
    out.update(exp25_tables)
    sensitivity = scoring_sensitivity.build(matrices)
    labels = {'registered': 'Registered aliases', 'full_normalized': 'Full, normalized',
              'full_verbatim': 'Full, verbatim', 'all_arguments': 'Include query'}
    sensitivity_rows = [f"{NAMES[d['model']]} & {labels[d['rule']]} & {frac(d['matched'])} & "
                        f"{frac(d['unmatched'])} & {100*d['difference'][0]:.1f} & "
                        f"{interval(d['difference'][1:])}" + r' \\' for d in sensitivity]
    out['sensitivity_table.tex'] = '\n'.join([
        r'\begin{center}\small\begin{longtable}{@{}llrrrl@{}}',
        r'\caption{Post-collection scoring sensitivity. Differences and paired field-bootstrap '
        r'intervals are percentage points. Same trials and field clusters throughout.}\\',
        r'\toprule Model & Scoring & M & U & Difference & 95\% CI \\\midrule',
        *sensitivity_rows, r'\bottomrule\end{longtable}\end{center}', ''])
    entries = bib_entries(Path('paper/refs.bib').read_text())
    entries.update(bib_entries((FOLDER / 'additional_refs.bib').read_text()))
    texts = '\n'.join((FOLDER / name).read_text() for name in ('main.tex', 'supplement.tex'))
    keys = sorted({key for m in re.finditer(r'\\cite\w*\{([^}]+)\}', texts) for key in m[1].split(',')})
    missing = set(keys) - entries.keys()
    if missing: raise ValueError(f'missing citations: {missing}')
    out['refs.bib'] = '% Generated selected bibliography; edit the source entries.\n\n' + '\n\n'.join(entries[k] for k in keys) + '\n'
    out['evidence_lock.json'] = json.dumps({
        'schema_version': 1,
        'scope': 'Fresh tables and source-edit detection; not semantic review or author approval.',
        'manuscripts': {(FOLDER / name).as_posix(): evidence.digest(FOLDER / name)
                        for name in ('main.tex', 'supplement.tex')},
        'selection_sha256': evidence.digest('data/artifact_selection.json'),
        'generated_sha256': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in out.items()},
        'scoring_sensitivity': sensitivity,
    }, indent=2, allow_nan=False) + '\n'
    return out


def check_or_write(write=False):
    stale = []
    for name, text in outputs().items():
        path = FOLDER / name
        if write:
            path.write_text(text)
        elif not path.exists() or path.read_text() != text:
            stale.append(str(path))
    if stale:
        raise ValueError('stale journal artifacts: ' + ', '.join(stale))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true')
    action.add_argument('--check', action='store_true')
    args = parser.parse_args()
    check_or_write(args.write)
    print('Journal tables, numbers and bibliography ' + ('regenerated.' if args.write else 'verified fresh.'))
