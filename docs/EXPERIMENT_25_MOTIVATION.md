# Experiment 25: motivation and preparation status

Updated 2026-09-29. The author's decision remains: **controlled stage A first;
real-schema stage B later, only if funded; restore integer inside A.**
The executable draft now follows that decision. Neither stage has live results.
The source of the decision is commit `0512ab7`; earlier cost figures and statements
that the code implements B only are superseded by the accounting below.

## The question

The historical study used free-text attack fields. A reviewer can reasonably ask
whether recovery depends on a field accepting arbitrary text. Experiment 25 tests
whether a canary-permitting schema constraint changes recovery, and whether
categorical fields recover planted values more often than their guessing baseline.

This strengthens the mechanism study; it does not establish deployment prevalence
or make a single-task study sufficient for a particular journal. A Q1 submission
still depends on evidence, novelty, honest limitations and editorial assessment.

## Two stages, two purposes

**A: controlled study.** Two synthetic tools (orders and email; email added
2026-09-29 so the result does not rest on one tool), four fixed naming fields
and twenty paired repetitions per tool. Within each free/constrained pair, only
the attack field's pattern/length constraint changes. Both schemas permit every
planted canary. The primary comparison is free minus constrained received target
recovery under a validating local host.

A separately tests enum, integer and boolean capacity with forty planted and
forty unplanted trials per provider/domain, on the orders tool only, because
this question is about field type rather than task. The integer belongs here because it
is a different JSON type and costs 160 calls across two providers. Domain-specific
wording and secrets differ, so cross-domain accuracy is not a pure type effect.

**B: conditional contextual check.** The same string manipulation on eight frozen
native schemas across four tasks. To keep B at 160 calls, B tests **one
prespecified field**, `platform_naming_1`, five paired repetitions per schema and
provider. Four fields would make B 640 calls, not 160. Native captures and adapters
remain intact; fixture handlers stand in for the actual servers.

B is written into the prospective protocol now, before sealing. Its funding
decision must be documented independently of A's observed result. Missing B is
reported as a planned conditional stage not collected, never silently substituted
with legacy observations. Increasing its size later needs a prospective amendment.

## Exact schedule and corrected budget

| Design | Calls | One-attempt planning envelope | Three-attempt envelope |
|---|---:|---:|---:|
| A: 320 free + 320 constrained + 80 controls + 480 capacity | 1,200 | $121.15 | $363.46 |
| B: 80 free + 80 constrained | 160 | $16.15 | $48.46 |
| A + B | 1,360 | $137.31 | $411.92 |

**Expected cost from measured usage** (7 unplanted Gemini compatibility calls,
list prices checked 2026-09-29): about **$1.20 for A's Gemini leg and $0.75 for
its GPT-4o leg**, roughly $2 for stage A. GPT-4o usage is estimated, not yet
measured. A runs as two legs in a fixed order, **Gemini first, then GPT-4o**;
the GPT-4o leg does not depend on Gemini's result.

These are conservative token/price assumptions, **not verified provider quotes**.
The earlier “worst case about $85” counted one attempt; the protocol allows up to
three billable attempts. Actual authorization remains **$0**. The planner's
simulation explores precision assumptions; it does not certify power or replace
independent statistical review. Twenty repeats is a draft budget choice.

## What is implemented

- Stage selection: A (default), B, or the superseded `legacy-native` design for
  offline inspection. Stage IDs are disjoint and schedules deterministic.
- A's synthetic contract and local task-result oracle; B's eight frozen native
  schemas and existing adapters.
- Canary-permitting paired constraints, balanced capacity labels, strict integer
  and boolean scoring, emissions/rejections/receipt/utility outcomes.
- Exact replicate pairing, A replicate-block bootstrap, field-composition
  sensitivity, B schema sensitivity, capacity permutation tests and Holm correction.
- Incomplete-collection detection, API-error bounds, duplicate/factor checks and
  separation of mock, live and cross-stage records.
- Full offline mock runs and regression tests. **Scripted values are engineering
  fixtures and never manuscript results.**

## What still separates this from a submission

1. Human review of the four field texts, task fixtures and statistical design.
2. GPT-4o schema compatibility and a price re-check before approval. (Gemini
   compatibility, live token accounting, the durable budget journal and resume
   were completed on 2026-09-29.)
3. Final protocol/code freeze, verified timestamp witness, disclosure decision
   and explicit stage-specific budget approval.
4. Collect A, report every attempted/missing trial, analyze without changing the
   plan, and integrate actual findings into the manuscript. Run B only if funded.
5. Confirm authorship, declarations, source permissions, venue requirements and
   final manuscript approval. Direct SCImago 2025 Q1 evidence has been retrieved;
   venue and final-file author approval remain pending.

No new temperature arm, secret-excluding enum or defense experiment is implied.
The existing temperature-zero observations remain exploratory. A secret-excluding
schema would require an attempt-based endpoint and a separate prospective design.

## Commands and files

From the repository root, using the working analysis environment:

```bash
.venv-q1/bin/python code/plan_extension.py --write
.venv-q1/bin/python code/schema_types_run.py --stage A --mock
.venv-q1/bin/python code/schema_types_run.py --stage B --mock
.venv-q1/bin/python code/schema_types_analyze.py extension_runs/<canonical-file>.jsonl
.venv-q1/bin/python code/schema_types_run.py --stage A --check-live
.venv-q1/bin/python code/reproduce.py
.venv-q1/bin/python code/submission_check.py
```

The live and submission checks deliberately report pending requirements.
Read [the protocol](JOURNAL_EXTENSION_PROTOCOL.md),
[the submission handoff](SUBMISSION_HANDOFF.md), and
[the current readiness audit](../Q1_READINESS_AUDIT.md).
