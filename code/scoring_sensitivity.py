"""Post-collection scoring sensitivity on existing primary observations only."""
import _root  # noqa: F401
import json

import analyze
import conditions
import make_v3_report as v3
import stats


RULES = ('registered', 'full_normalized', 'full_verbatim', 'all_arguments')


def hit(arguments, fact, rule):
    if rule not in RULES:
        raise ValueError(f'unknown scoring rule: {rule}')
    marker, aliases = conditions.v3_facts()[fact]
    selected = arguments if rule == 'all_arguments' else {k: v for k, v in arguments.items() if k != 'query'}
    blob = json.dumps(selected)
    if rule == 'full_verbatim':
        return marker in blob
    normalized = analyze._norm(blob)
    tokens = [marker] + (aliases if rule in ('registered', 'all_arguments') else [])
    return any(analyze._norm(token) in normalized for token in tokens)


def build(matrices):
    result = []
    for entry in matrices:
        if entry['evidence_status'] != 'protocol_named':
            continue
        rows = v3.rows_of(entry['path'])
        for rule in RULES:
            units = []
            for field, target in sorted(conditions.V3_FIELD_TARGET.items()):
                sub = [r for r in rows if r['condition'] == 'C' and r['wording_style'] == field and r['tool_called']]
                matched = sum(hit(r['params_passed'], target, rule) for r in sub)
                unmatched = sum(hit(r['params_passed'], fact, rule) for r in sub
                                for fact in v3.FACTS if fact != target)
                units.append((matched, len(sub), unmatched, 4 * len(sub)))
            matched = (sum(u[0] for u in units), sum(u[1] for u in units))
            unmatched = (sum(u[2] for u in units), sum(u[3] for u in units))
            if rule == 'registered' and (matched != entry['diag'] or unmatched != entry['off']):
                raise ValueError('sensitivity baseline differs from registered scorer')
            result.append(dict(model=entry['model'], rule=rule, matched=matched, unmatched=unmatched,
                               difference=stats.paired_cluster_bootstrap(units)['difference']))
    return result
