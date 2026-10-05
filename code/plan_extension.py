"""Stage A/B cost and paired-block precision planning. Offline, no model evidence."""
import _root  # noqa: F401
import argparse
import json
from pathlib import Path
import numpy as np
import schema_types_design as design


def simulate(reps, delta, simulations=300, bootstraps=400, field_sd=.12, block_sd=.10, shared_probability=.5):
    """Fixed four fields, shared canary blocks; positive within-pair correlation.

    This is an assumption sensitivity analysis, not a sample-size guarantee.
    Free recovery averages .60; delta is free minus constrained recovery.
    """
    rng = np.random.default_rng(928 + reps + round(delta * 1000) + round(block_sd * 100))
    widths, covered, supported = [], [], []
    for _ in range(simulations):
        field = rng.normal(0, field_sd, (4, 1))
        block = rng.normal(0, block_sd, (1, reps))
        free = np.clip(.60 + field + block, .001, .999)
        constrained = np.clip(.60 - delta + field + block, .001, .999)
        u = rng.uniform(size=(4, reps))
        independent = rng.uniform(size=(4, reps))
        coupled = rng.uniform(size=(4, reps)) < shared_probability
        v = np.where(coupled, u, independent)
        observed = ((u < free).astype(float) - (v < constrained)).mean(axis=0)
        samples = observed[rng.integers(0, reps, (bootstraps, reps))].mean(axis=1)
        lo, hi = np.quantile(samples, [.025, .975])
        widths.append(float((hi - lo) / 2))
        covered.append(bool(lo <= (free - constrained).mean() <= hi))
        supported.append(bool(lo > 0))
    return dict(reps=reps, assumed_attenuation=delta, field_sd=field_sd, block_sd=block_sd,
                simulations=simulations, bootstraps=bootstraps, shared_probability=shared_probability,
                p95_half_width=float(np.quantile(widths, .95)),
                interval_excludes_zero_frequency=float(np.mean(supported)),
                conditional_coverage=float(np.mean(covered)))


def build():
    per_attempt = (6000 * 10 + 1024 * 40) / 1_000_000
    stages = {}
    for stage in ("A", "B", "legacy-native"):
        counts = design.expected_counts(stage)
        calls = sum(counts.values())
        stages[stage] = dict(calls_by_arm=counts, calls=calls,
            one_attempt_envelope_usd=round(calls * per_attempt, 2),
            three_attempt_envelope_usd=round(calls * per_attempt * 3, 2))
    grid = [simulate(reps, delta, block_sd=sd, shared_probability=coupling) for reps in (10, 20, 40)
            for delta in (0, .10, .20, .40) for sd in (.10, .25) for coupling in (0, .5, .9)]
    return dict(status="DRAFT; not registered; no paid-run authorization", seed=928,
        selected_reps=20, selection_basis="Budget-constrained prospective candidate; independent statistical review pending, not selected by a passing power gate",
        stages=stages, combined_A_B_calls=stages['A']['calls'] + stages['B']['calls'],
        simulations=grid, pricing_assumptions=dict(input_tokens_max=6000, output_tokens_max=1024,
            input_usd_per_million_ceiling=10, output_usd_per_million_ceiling=40, attempts_max=3,
            verified_current_prices=False),
        limitations="Four fixed fields on two synthetic tasks (orders, email); capacity on orders only. Independent to strongly coupled within-pair draws are sensitivity assumptions; no deployment-population inference. B has one fixed field and no capacity/control tranche. Live input-token accounting still requires implementation and verification.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    output = json.dumps(build(), indent=2, allow_nan=False) + '\n'
    if args.write:
        Path('data/extension_design.json').write_text(output)
        print('wrote data/extension_design.json; no API calls')
    else:
        print(output)
