"""Offline statistical appendix and independent primary-count verification."""
import _root  # noqa: F401
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

import conditions
import evidence
import make_v3_report as v3
import stats


def independent_counts(path):
    """Independent implementation: do not call the production recovery scorer."""
    counts = Counter()
    normalize = lambda s: re.sub('[^a-z0-9]', '', s.lower())
    for row in evidence.read_jsonl(path):
        if 'error' in row or row.get('tool_called') is not True:
            continue
        arguments = row.get('params_passed') or {}
        blob = normalize(json.dumps({k: value for k, value in arguments.items() if k != 'query'}))
        matched = conditions.V3_FIELD_TARGET.get(row['wording_style'])
        hits = {f: any(normalize(token) in blob for token in [marker] + aliases)
                for f, (marker, aliases) in conditions.v3_facts().items()}
        if row['condition'] == 'D':
            counts['control_calls'] += 1
            counts['control_any'] += any(hits.values())
        elif row['condition'] == 'C' and matched:
            counts['diagonal_n'] += 1
            counts['diagonal_k'] += hits[matched]
            counts['off_n'] += len(hits) - 1
            counts['off_k'] += sum(hit for fact, hit in hits.items() if fact != matched)
    return dict(counts)


def secondary(matrices):
    result, records = [], []
    for entry in matrices:
        rows = [r for r in v3.rows_of(entry['path']) if r['condition'] == 'C'
                and r['tool_called'] and r['wording_style'] in v3.TARGET]
        for stratum in ('all', 'naming', 'adjacent'):
            sub = [r for r in rows if stratum == 'all' or v3.EXPLICIT[r['wording_style']] == stratum]
            for fact in v3.FACTS:
                diagonal = [r for r in sub if v3.TARGET[r['wording_style']] == fact]
                off = [r for r in sub if v3.TARGET[r['wording_style']] != fact]
                if not diagonal or not off:
                    continue
                dk, dn = sum(v3.recovered(r, fact) for r in diagonal), len(diagonal)
                ok, on = sum(v3.recovered(r, fact) for r in off), len(off)
                result.append(dict(model=entry['model'], stratum=stratum, fact=fact,
                                   diagonal=[dk, dn], offdiag=[ok, on],
                                   wilson=stats.wilson(dk, dn),
                                   difference_newcombe=stats.newcombe_diff(dk, dn, ok, on),
                                   p=stats.fisher_exact_greater(dk, dn, ok, on)))
        for row in rows:
            for fact in v3.FACTS:
                records.append(dict(y=int(v3.recovered(row, fact)),
                                    matched=int(v3.TARGET[row['wording_style']] == fact),
                                    field=row['wording_style'], fact=fact, provider=entry['model']))
    # The protocol did not specify the correction family across gradient strata.
    # Keep primary per-fact family separate from the post-collection gradient family.
    for strata in ({'all'}, {'naming', 'adjacent'}):
        family = [r for r in result if r['stratum'] in strata]
        for row, p in zip(family, stats.holm([r['p'] for r in family])):
            row['p_holm'] = p
            row['family_size'] = len(family)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter('always')
        model = BinomialBayesMixedGLM.from_formula(
            'y ~ matched', {'field': '0+C(field)', 'fact': '0+C(fact)', 'provider': '0+C(provider)'},
            pd.DataFrame(records), vcp_p=1, fe_p=2)
        size = model.k_fep + model.k_vcp + model.k_vc
        fitted = model.fit_vb(mean=np.zeros(size), sd=np.ones(size), verbose=False)
    mixed = dict(method='Bayesian variational logistic; fe_p=2, vcp_p=1; zero means/unit SD initialization',
                 converged=bool(fitted.optim_retvals.get('success')),
                 fixed_effects=dict(zip(model.exog_names, map(float, fitted.fe_mean))),
                 fixed_effect_sd=dict(zip(model.exog_names, map(float, fitted.fe_sd))),
                 warnings=[str(w.message) for w in observed],
                 limitation='Two providers; repeated facts per trial; separation and priors limit interpretation. Not primary evidence.')
    return result, mixed


def temperature_zero():
    path = 'runs/v2_matrix_openai_t0-live-20260810-184331.jsonl'
    rows = evidence.read_jsonl(path)
    facts = conditions.OMNIBUS_FACTS
    target = conditions.V2_FIELD_TARGET
    counts = Counter()
    for row in rows:
        if 'error' in row or not row.get('tool_called'):
            continue
        import analyze
        blob = analyze._norm(analyze._field_args(row))
        hits = {f: any(analyze._norm(w) in blob for w in [marker] + aliases)
                for f, (marker, aliases) in facts.items()}
        if row['condition'] == 'D':
            counts['neutral_calls'] += 1
            counts['neutral_any'] += any(hits.values())
        elif row['wording_style'] in target:
            t = target[row['wording_style']]
            counts['diagonal_n'] += 1
            counts['diagonal_k'] += hits[t]
            counts['off_n'] += len(hits) - 1
            counts['off_k'] += sum(v for f, v in hits.items() if f != t)
    return dict(path=path, sha256=evidence.digest(path), rows=len(rows),
                temperatures=sorted({r['temperature'] for r in rows}), counts=dict(counts),
                status='exploratory v2; different fixtures and collection time; not a causal temperature contrast with v3')


def build():
    matrices = [d for d in v3.pick(v3.canonical('runs/v3_matrix_*-live-*.jsonl'), v3.matrix_stats)
                if d['evidence_status'] == 'protocol_named']
    independent = []
    for d in matrices:
        check = independent_counts(d['path'])
        assert (check['diagonal_k'], check['diagonal_n']) == d['diag']
        assert (check['off_k'], check['off_n']) == d['off']
        assert (check['control_any'], check['control_calls']) == d['ctrl_calls']
        # Independent NumPy implementation of resampling; agreement to 3 pp is
        # a diagnostic, not a replacement for the frozen Python RNG estimator.
        units = np.array([(*d['per_field'][w], *d['per_field_off'][w]) for w in sorted(d['per_field'])])
        sampled = units[np.random.default_rng(928).integers(0, len(units), (100000, len(units)))].sum(axis=1)
        difference = sampled[:, 0] / sampled[:, 1] - sampled[:, 2] / sampled[:, 3]
        ci = np.quantile(difference, [.025, .975])
        assert np.max(np.abs(ci - np.array(d['cluster']['difference'][1:]))) < .03
        independent.append(dict(model=d['model'], counts=check, production_ci=d['cluster']['difference'],
                                independent_ci=ci.tolist(), loo_difference=d['loo_difference'],
                                fields=d['clusters'], control_ci_call_level_descriptive=stats.wilson(*d['ctrl_calls'])))
    per_fact, mixed = secondary(matrices)
    return dict(schema_version=1, primary_decision=v3.primary_decision(matrices),
                primary_crosscheck=independent, per_fact=per_fact, hierarchical=mixed,
                temperature_zero=temperature_zero(),
                generic_status='Descriptive any-canary endpoint only: no semantic target, so registered generic diagonal rule is undefined.',
                inference_limit='Per-fact Fisher/Wilson/Newcombe tests are the registered call-level analyses, not cluster-robust tests. Gradient Holm-family choice is a disclosed post-collection implementation choice.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    text = json.dumps(build(), indent=2, allow_nan=False) + '\n'
    if args.write:
        Path('data/q1_analysis.json').write_text(text)
        print('wrote data/q1_analysis.json; independent primary checks passed')
    else:
        print(text)


if __name__ == '__main__':
    main()
