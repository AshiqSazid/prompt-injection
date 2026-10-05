# Independent review package — awaiting a human reviewer

Updated 2026-09-29. No reviewer has been contacted and no independent human
approval is claimed. Automated independent numerical cross-checks are not an
independent assessment of novelty, ethics or scientific sufficiency. This file
is a brief the authors may send after approving the recipient and release scope.

The experiment-specific review questions now appear in
[EXPERIMENT_25_REVIEW_BRIEF.md](EXPERIMENT_25_REVIEW_BRIEF.md). The author chose
controlled A first and funding-conditional B; neither has live observations.
The old broad defense/task proposal is not part of the reduced call budget.

## Materials to review

- Active manuscript: `journal_paper/main.tex` and its PDF; supplement alongside it.
- Evidence chain: `data/artifact_selection.json`, `data/evidence_inventory.json`,
  `journal_paper/evidence_lock.json`, selected historical raw responses.
- Analysis: `code/stats.py`, `code/q1_analysis.py`, `data/q1_analysis.json`,
  `code/scoring_sensitivity.py`, `docs/DEVIATIONS.md` and original `protocol-v3.md`.
- Extension: `docs/JOURNAL_EXTENSION_PROTOCOL.md`, `data/extension_design.json`,
  `code/plan_extension.py`. The new `code/extension_harness.py` and
  `data/extension_smoke.json` are engineering fixtures, not collected observations.
- Venue: `docs/TDSC_TARGET.md`; publication gates in `data/submission_decisions.json`.

Do not send the entire workspace: it contains unrelated personal documents and
may contain credentials or identifying history. `code/release_audit.py` supplies
private checks, not publication permission or a complete secrets certificate.

## Reviewer questions and current assessment

| Priority | Question for reviewer | Current limitation or evidence |
|---|---|---|
| Blocking scientific scope | Is a one-task, seven-purposive-field selectivity study sufficiently general and substantial for TDSC? | Existing findings are bounded measurements; no native four-task extension has been collected. Recommend retaining the extension unless a domain reviewer supports the narrower route. |
| Blocking statistical interpretation | Does the paired field bootstrap support the stated estimand, with just seven clusters and dependent fact checks? | Independent numerical implementation agrees; that does not validate population inference. Review field heterogeneity, leave-one-out ranges and simultaneous two-provider decision rule. |
| Blocking prior-art assessment | Is selectivity itself a defensible advance over parameter extraction and existing MCP benchmarks? | Ten-source focused review is available; novelty is not mechanism discovery, and an exhaustive search has not been certified. |
| High | Are protocol deviations visible and appropriately downgraded? | Bootstrap implementation corrected after collection; generic-stratum decision rule ambiguous; unplanted controls cover six of eight fields. Do not call all registered hypotheses confirmed. |
| High | Are security and utility endpoints separated adequately? | Historical emitted markers do not establish dispatch, handler receipt or task utility. Mock transport and scripted local tests cannot fill that evidence gap. |
| High | Can the historical scanner comparison support more than a provisional observation? | Raw classifier text is absent and malformed outputs could have become negative votes. Strict new parsing cannot validate old votes. |
| High | Are extension sample size and intervals robust to design assumptions? | The simulation's candidate repetitions depend on assumed effect and heterogeneity. Review cross-provider dependence, schema/field clustering, false-positive behavior and coverage before freezing. |
| High | Does the release policy meaningfully prevent disclosure while retaining utility? | A structural allowlist can still transmit a secret in permitted strings. New offline regression tests deliberately retain this failure mode; no prevention efficacy is claimed. |
| Required author review | Are consent, disclosure, authorship, licensing, AI-use and prior-publication declarations accurate? | Author-supplied facts and approvals remain missing; software cannot infer them. |

## Reviewer response form

Record each response with reviewer name/affiliation, expertise, conflicts,
review date, reviewed source hashes, issue, severity, requested action, author
response, verification evidence and disposition (open/resolved/accepted limitation).
Give separate judgments for numerical correctness, statistical interpretation,
scientific contribution and ethics. “Tests passed” is not an answer to all four.
Do not record `statistical_review` or `literature_and_novelty` as confirmed until
an actual review has been completed and its evidence retained.

## Reproduction commands

Use the locked environment documented in the repository; do not run provider
drivers. These commands do not collect model observations:

```bash
.venv-q1/bin/python code/reproduce.py
.venv-q1/bin/python code/reproduce.py --papers-only
.venv-q1/bin/python code/extension_harness.py
.venv-q1/bin/python code/submission_check.py
```

The final command is expected to fail while author/reviewer gates remain open.
Keep that distinction in any review report.
