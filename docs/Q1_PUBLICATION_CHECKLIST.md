# Q1 publication gates and claim-to-evidence matrix

Updated 2026-09-29. This checklist distinguishes implemented artifact repairs from
scientific evidence that still requires collection or independent judgment.

The active focused draft and supplement are in `journal_paper/`. Its ten
references have a targeted claim-level review in `docs/JOURNAL_LITERATURE_REVIEW.md`;
this does not mark the earlier 35-reference audit complete. The machine-readable
author/venue record is `data/submission_decisions.json`, checked separately by
`code/submission_check.py`. Outstanding human decisions remain outstanding.

## Claim-to-evidence map

| Claim | Evidence and computation | Allowed interpretation |
|---|---|---|
| Field-to-fact selectivity | Selected v3 OpenAI/Google matrix logs; `make_v3_report.py`; independent `q1_analysis.py` | Supported primary rule for these fixtures and providers, after disclosed implementation correction |
| Neutral control | 160 calls per provider, five checks each | No observed recovery, not zero population risk |
| Generic field | 20 calls per provider | No observed any-canary recovery; no defined diagonal inference |
| Temperature robustness | `v2_matrix_openai_t0-live-20260810-184331.jsonl` | Exploratory descriptive arm; cannot isolate a temperature effect from changed fixtures/time |
| Published scanner gap | `scan_invariant.py` and saved boolean votes | Provisional: raw judge text was not retained and malformed historical answers cannot be ruled out; not current hosted scanning or all defenses |
| Detector AUC / projected reduction | `data/defense_eval.json` | Nine authored positives versus corpus negatives; retrospective projection, not measured prevention or task utility |
| External schema contexts | `data/real_tools.json`, selected real-schema logs | Rendered-listing reconstruction; native types/nesting not preserved |
| Transport | No-network `test_q1.McpRoundTrip` and repaired probe | Mock plumbing with correlated handler receipt; not a commercial-client or live-model result |
| Human validation | Existing 60-row gate sample, labels and attestation | One coauthor, narrow stratified gate validation only |
| Timestamp precedence | Immutable v3 protocol, digest, `.ots`, deviations record | Historical calendar-lodging record; independent anchored-proof verification remains a gate |

## Registered v3 analysis completion

- [x] Primary paired field bootstrap, number of clusters and leave-one-field-out
  sensitivity; both conditional and ITT counts.
- [x] Per-fact Wilson/Fisher/Holm/Newcombe on the two protocol-named providers.
- [x] Hierarchical logistic sensitivity fit, convergence, priors and caveats recorded.
- [x] Naming/adjacent strata and explicit post-collection Holm-family definition.
- [x] Generic any-canary outcomes separately; original decision-rule ambiguity disclosed.
- [x] Unplanted any-canary counts rather than a fact-check numerator divided by calls.
  Full same-field control coverage is **not complete**: six of eight fields were
  collected; platform-adjacent and region-adjacent controls are missing. Stage
  metadata completeness refers to the configured six-field stage only.
- [ ] Independent statistician review of repeated fact outcomes, small cluster counts,
  multiplicity choices and scope of inference. A passing script is not that review.

## Required before new paid experiments

- [ ] Exact native source schemas, revisions, licenses, field wording, task fixtures
  and deterministic utility oracles frozen and reviewed.
- [ ] Model availability, served IDs, real provider prices and billable-token rules
  verified; named models must not be silently substituted.
- [ ] Precision simulation reviewed under alternative dependence/heterogeneity;
  final sample size frozen before observations.
- [ ] Budget owner approves a numerical cap; worst-case request reservation and
  per-attempt cost accounting tested. Current permission remains **US$0**.
- [ ] Prospective protocol/code/config hashes externally witnessed before any data.
- [ ] Separate decisions documented for disclosure and any vendor-bound schema upload.

## Required before submission

- [x] Fresh-count/denominator checks, fixed evidence selection, model-prefix tests,
  malformed-input tests, collision/resume tests and actual MCP round-trip tests.
- [x] Python 3.12 analysis lock and offline CI configuration; local regression and
  temporary clean manuscript builds exercised. Hosted CI has not been run here.
  The exhaustive local inventory includes ignored historical mock outputs; clean
  reproduction requires exact agreement for non-mock artifacts, not their presence.
- [x] 35 cited records fetched from primary/public source URLs, with citation
  contexts exported. 31 titles automatically match; four webpage-title differences
  require contextual interpretation, not automatic BibTeX replacement.
- [ ] Verify every author's spelling/order, archival publication venue/year/DOI and
  each load-bearing claim against the actual cited passage. Abstract/title matches
  are insufficient. The full passage-level literature review remains unfinished.
- [ ] Update literature through submission date. MSB already includes out-of-scope
  parameter attacks; HiddenLayer establishes the extraction mechanism. Avoid
  “first parameter attack,” “no existing benchmark,” and universal defense claims.
- [ ] Complete the approved extension and publish null/negative findings with
  stopping/exclusion accounting, or narrow the manuscript to existing evidence.
- [ ] Record actual coordinated-notification outcome or a justified author decision.
  Prior public Git history does not constitute vendor coordination.
- [ ] Verify timestamp anchoring without modifying the historical proof in place.
- [ ] Complete anonymous export, PDF metadata, Git-history and source-license review.
  Exclude `.git`, `.env`, caches, local virtual environments and unrelated student
  PDF/DOCX files; do not rewrite the research repository's public history.
- [x] Retrieve direct category/year SJR evidence: TDSC is 2025 Q1 in both listed
  categories. Retrieve publisher requirements and prepare IEEE-format files.
- [ ] Author confirmation of venue, final template settings and exact files.

## Venue and novelty checks

The current preparation target is **IEEE TDSC**, regular-paper route. Direct
SCImago 2025 Q1 evidence and current publisher instructions were retrieved on
2026-09-29; the main manuscript now uses IEEEtran and a separate supplement.
See [TDSC_TARGET.md](TDSC_TARGET.md). No submission has been made. The earlier
Computers & Security recommendation remains withdrawn; this revision does not
reassess that journal's eligibility.

Experiment 25 now has a controlled stage A (1,200 calls on orders and email
tools, including integer; Gemini leg first, then GPT-4o) and a
fixed funding-conditional stage B (160 calls across native contexts). Both are
validated with mocks only. Field/fixture review, live execution hardening,
provider checks, registration and collection are still required. See the
[prospective protocol](JOURNAL_EXTENSION_PROTOCOL.md) and
[review brief](EXPERIMENT_25_REVIEW_BRIEF.md).

Primary-source novelty checks support the following narrower framing:

- HiddenLayer already demonstrates parameter-mediated extraction and fake
  function variants. The new contribution must be the controlled selective-recovery
  measurement, not the existence of extraction.
  [HiddenLayer research](https://www.hiddenlayer.com/research/beyond-mcp-expanding-agentic-function-parameter-abuse).
- MSB §4.2 and Appendix B.1.2 already define and demonstrate out-of-scope parameter
  attacks. The v3 multi-fact matching matrix is a design distinction; a categorical
  assertion that MSB has no relevant parameter task is untenable.
  [MSB full text](https://arxiv.org/html/2510.15994v1).
- Further comparison candidates found in this pass include protocol-level security
  analysis and runtime enforcement. They are not automatically incorporated as
  supporting citations without passage review.
  [Breaking the Protocol](https://arxiv.org/abs/2601.17549),
  [Runtime Policy Enforcement](https://www.mdpi.com/2079-9292/15/13/2829),
  [Securing the Tool Layer](https://aclanthology.org/2026.acl-industry.58/).

The literature skills guided the distinction between metadata lookup and
passage-level verification. Their credit-consuming Firecrawl operations were not
used under the zero-spend constraint; public HTTP and free web access were used.
